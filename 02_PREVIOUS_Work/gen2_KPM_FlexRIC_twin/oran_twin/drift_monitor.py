from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass(frozen=True)
class DriftAssessment:
    drift_score: float
    drift_status: str
    drift_type: str
    adaptation_action: str
    model_profile_id: str
    lifecycle_stage: str
    retraining_priority: str
    automation_mode: str
    reasons: list[str]


class DriftMonitor:
    """Window-based model drift monitor for O-RAN KPI streams."""

    def __init__(self, baseline_window: int = 24, recent_window: int = 12) -> None:
        self.baseline_window = baseline_window
        self.recent_window = recent_window
        self.history: dict[tuple[str, str], deque[dict[str, float]]] = defaultdict(
            lambda: deque(maxlen=baseline_window + recent_window)
        )
        self.last_drift_seen: dict[tuple[str, str], int] = {}
        self.metrics = [
            "latency",
            "jitter",
            "throughput",
            "loss",
            "prb",
            "handover",
            "edge_delay",
            "backhaul",
            "bler",
        ]

    def assess(self, row: dict[str, object]) -> DriftAssessment:
        key = (str(row.get("cell_id", row.get("id", "unknown"))), str(row.get("service_class", row.get("service", "unknown"))))
        hist = self.history[key]
        current = self._extract(row)
        hist.append(current)

        min_samples = self.baseline_window + max(4, self.recent_window // 2)
        if len(hist) < min_samples:
            return DriftAssessment(
                0.0,
                "warming_up",
                "none",
                "collect_more_samples",
                self._profile_id(key, "baseline"),
                "baseline_initialization",
                "low",
                "monitor_only",
                ["insufficient_history"],
            )

        baseline = list(hist)[: self.baseline_window]
        recent = list(hist)[-self.recent_window :]
        reasons: list[str] = []
        shifts: list[float] = []
        sustained = 0
        abrupt = 0

        for metric in self.metrics:
            base_values = [item[metric] for item in baseline]
            recent_values = [item[metric] for item in recent]
            base_mean = sum(base_values) / len(base_values)
            recent_mean = sum(recent_values) / len(recent_values)
            variance = sum((value - base_mean) ** 2 for value in base_values) / len(base_values)
            sigma = max(0.001, variance**0.5)
            normalized_shift = abs(recent_mean - base_mean) / sigma
            relative_shift = abs(recent_mean - base_mean) / max(abs(base_mean), 0.001)
            score = min(1.0, max(normalized_shift / 6.5, relative_shift / 1.25))
            if score >= 0.35:
                reasons.append(f"{metric}_distribution_shift")
            shifts.append(score)

            recent_outliers = sum(1 for value in recent_values if abs(value - base_mean) / sigma > 3.4)
            if recent_outliers >= max(3, len(recent_values) // 2):
                sustained += 1
            if recent_values and abs(recent_values[-1] - base_mean) / sigma > 5.2:
                abrupt += 1

        drift_score = round(min(1.0, sum(sorted(shifts, reverse=True)[:4]) / 4.0), 4)
        drift_status = self._status(drift_score)
        drift_type = self._classify(drift_score, sustained, abrupt, key, self._time(row))
        adaptation_action = self._adaptation(drift_status, drift_type)
        lifecycle_stage, retraining_priority, automation_mode = self._lifecycle_plan(drift_status, drift_type)
        model_profile_id = self._profile_id(key, drift_type if drift_type != "none" else "baseline")
        if drift_status == "stable":
            reasons = []
        elif not reasons:
            reasons = ["multi_metric_distribution_shift"]

        if drift_status in {"warning", "drifted"}:
            self.last_drift_seen[key] = self._time(row)

        return DriftAssessment(
            drift_score=drift_score,
            drift_status=drift_status,
            drift_type=drift_type,
            adaptation_action=adaptation_action,
            model_profile_id=model_profile_id,
            lifecycle_stage=lifecycle_stage,
            retraining_priority=retraining_priority,
            automation_mode=automation_mode,
            reasons=sorted(set(reasons)),
        )

    def reset(self) -> None:
        self.history.clear()
        self.last_drift_seen.clear()

    def _extract(self, row: dict[str, object]) -> dict[str, float]:
        return {
            "latency": self._float(row, "latency_ms", "latency"),
            "jitter": self._float(row, "jitter_ms", "jitter"),
            "throughput": self._float(row, "throughput_mbps", "throughput"),
            "loss": self._float(row, "packet_loss_pct", "loss"),
            "prb": self._float(row, "prb_util_pct", "prb"),
            "handover": self._float(row, "handover_fail_pct", "handover"),
            "edge_delay": self._float(row, "edge_delay_ms", "edgeDelay"),
            "backhaul": self._float(row, "backhaul_delay_ms", "backhaul"),
            "bler": self._float(row, "bler_pct", "bler"),
        }

    @staticmethod
    def _float(row: dict[str, object], *keys: str) -> float:
        for key in keys:
            if key in row:
                return float(row[key])
        return 0.0

    @staticmethod
    def _time(row: dict[str, object]) -> int:
        try:
            return int(float(row.get("t", 0)))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _status(score: float) -> str:
        if score >= 0.74:
            return "drifted"
        if score >= 0.45:
            return "warning"
        return "stable"

    def _classify(self, score: float, sustained: int, abrupt: int, key: tuple[str, str], t: int) -> str:
        if score < 0.45:
            return "none"
        previous = self.last_drift_seen.get(key)
        if previous is not None and t - previous > self.baseline_window:
            return "recurring"
        if abrupt >= 3:
            return "sudden"
        if sustained >= 4 and score >= 0.74:
            return "incremental"
        return "gradual"

    @staticmethod
    def _adaptation(status: str, drift_type: str) -> str:
        if status == "stable":
            return "keep_model"
        if status == "warming_up":
            return "collect_more_samples"
        if status == "warning":
            if drift_type == "recurring":
                return "prepare_known_model_profile"
            return "schedule_retraining"
        if drift_type == "sudden":
            return "freeze_automation_and_retrain"
        if drift_type == "incremental":
            return "switch_or_retrain_model"
        if drift_type == "recurring":
            return "reuse_known_model_profile"
        return "schedule_retraining"

    @staticmethod
    def _lifecycle_plan(status: str, drift_type: str) -> tuple[str, str, str]:
        if status == "warming_up":
            return "baseline_initialization", "low", "monitor_only"
        if status == "stable":
            return "model_current", "low", "normal_automation"
        if status == "warning" and drift_type == "recurring":
            return "known_profile_candidate", "medium", "guarded_automation"
        if status == "warning":
            return "retraining_scheduled", "medium", "guarded_automation"
        if drift_type == "sudden":
            return "model_quarantine", "critical", "freeze_closed_loop"
        if drift_type == "incremental":
            return "candidate_model_required", "high", "human_approved_automation"
        if drift_type == "recurring":
            return "known_profile_reuse", "medium", "guarded_automation"
        return "model_review_required", "high", "human_approved_automation"

    @staticmethod
    def _profile_id(key: tuple[str, str], profile_type: str) -> str:
        cell, service = key
        safe_type = profile_type.replace(":", "_")
        return f"{cell}_{service}_{safe_type}_profile"
