from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


FEATURES = [
    "latency_ms",
    "jitter_ms",
    "throughput_mbps",
    "packet_loss_pct",
    "prb_util_pct",
    "handover_fail_pct",
    "edge_delay_ms",
    "backhaul_delay_ms",
    "sinr_db",
    "bler_pct",
    "cqi",
    "harq_retx_pct",
    "rlc_buffer_kbytes",
    "mac_scheduler_delay_ms",
    "beam_quality_score",
    "timing_offset_us",
    "fronthaul_delay_ms",
    "rsrp_dbm",
    "rsrq_db",
    "rssi_dbm",
    "noise_floor_dbm",
    "evm_pct",
    "interference_power_dbm",
    "beam_misalignment_deg",
    "antenna_vswr",
    "rf_temperature_c",
    "rrc_setup_fail_pct",
    "rrc_reestab_rate_pct",
    "pdcp_discard_rate_pct",
    "pdcp_reordering_delay_ms",
    "sdap_qos_flow_drop_pct",
    "qfi_violation_pct",
    "session_drop_rate_pct",
    "mobility_pingpong_pct",
    "amf_registration_fail_pct",
    "amf_paging_delay_ms",
    "pdu_session_setup_ms",
    "pdu_session_fail_pct",
    "upf_cpu_util_pct",
    "upf_packet_drop_pct",
    "gtp_tunnel_loss_pct",
    "n3_rtt_ms",
    "n6_internet_rtt_ms",
    "transport_jitter_ms",
]


@dataclass
class SelfLearningAssessment:
    anomaly_score: float
    anomaly_detected: bool
    rca_prediction: str
    rca_confidence: float
    sample_count: int
    learning_mode: str
    reasons: list[str]


class OnlineMoments:
    """Numerically stable online mean/variance tracker."""

    def __init__(self) -> None:
        self.count = 0
        self.mean = 0.0
        self.m2 = 0.0

    def update(self, value: float) -> None:
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        delta2 = value - self.mean
        self.m2 += delta * delta2

    @property
    def variance(self) -> float:
        if self.count < 2:
            return 0.0
        return self.m2 / (self.count - 1)

    @property
    def std(self) -> float:
        return math.sqrt(max(0.0001, self.variance))

    def z_score(self, value: float) -> float:
        return (value - self.mean) / self.std

    def to_dict(self) -> dict[str, float | int]:
        return {"count": self.count, "mean": round(self.mean, 6), "m2": round(self.m2, 6)}

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "OnlineMoments":
        item = cls()
        item.count = int(data.get("count", 0))
        item.mean = float(data.get("mean", 0.0))
        item.m2 = float(data.get("m2", 0.0))
        return item


class OnlineSelfLearningModel:
    """Online anomaly/RCA learner for real-time O-RAN KPI streams.

    This is intentionally dependency-free. It is not a neural network; it is a
    production-friendly first self-learning layer that updates from streaming
    telemetry and replay labels. It gives the system a model-ready boundary
    before introducing heavier libraries such as scikit-learn, PyTorch, or River.
    """

    def __init__(self, warmup: int = 24, anomaly_z: float = 2.7) -> None:
        self.warmup = warmup
        self.anomaly_z = anomaly_z
        self.feature_stats: dict[str, dict[str, OnlineMoments]] = defaultdict(
            lambda: {feature: OnlineMoments() for feature in FEATURES}
        )
        self.root_cause_centroids: dict[str, dict[str, OnlineMoments]] = defaultdict(
            lambda: {feature: OnlineMoments() for feature in FEATURES}
        )
        self.root_cause_counts: Counter[str] = Counter()

    def assess(self, row: dict[str, object], learn: bool = True) -> SelfLearningAssessment:
        key = self._key(row)
        stats = self._stats_for_key(key)
        sample_count = min((stats[feature].count for feature in FEATURES), default=0)
        features = self._features(row)

        reasons: list[str] = []
        anomaly_score = 0.0
        if sample_count >= self.warmup:
            z_values = {}
            for feature, value in features.items():
                z = stats[feature].z_score(value)
                z_values[feature] = z
                directional_z = abs(z) if feature in {"throughput_mbps", "sinr_db"} else max(0.0, z)
                if directional_z >= self.anomaly_z:
                    reasons.append(f"learned_{feature}_z={z:.1f}")
                    anomaly_score += min(5.0, directional_z)
            anomaly_score = min(1.0, anomaly_score / 14.0)

        rca_prediction, rca_confidence = self._predict_root_cause(features)
        if rca_prediction != "unknown":
            reasons.append(f"learned_rca={rca_prediction}:{rca_confidence:.2f}")

        if learn:
            self.learn(row)

        mode = "warming_up" if sample_count < self.warmup else "online_learning"
        return SelfLearningAssessment(
            anomaly_score=round(anomaly_score, 4),
            anomaly_detected=anomaly_score >= 0.55,
            rca_prediction=rca_prediction,
            rca_confidence=round(rca_confidence, 4),
            sample_count=sample_count,
            learning_mode=mode,
            reasons=reasons,
        )

    def learn(self, row: dict[str, object]) -> None:
        key = self._key(row)
        features = self._features(row)
        self._stats_for_key(key)

        # Update normal baselines only from records that are not explicitly labeled as faults/attacks.
        if not self._bool(row.get("fault_active", False)) and not self._bool(row.get("aml_attack_active", False)):
            for feature, value in features.items():
                self.feature_stats[key][feature].update(value)

        root_cause = str(row.get("fault_type", "normal")).split("+", 1)[0]
        if root_cause and root_cause != "normal" and self._bool(row.get("fault_active", False)):
            self.root_cause_counts[root_cause] += 1
            self._centroid_for_cause(root_cause)
            for feature, value in features.items():
                self.root_cause_centroids[root_cause][feature].update(value)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    def to_dict(self) -> dict[str, object]:
        return {
            "type": "online_self_learning_v1",
            "features": FEATURES,
            "warmup": self.warmup,
            "anomaly_z": self.anomaly_z,
            "feature_stats": {
                key: {feature: moments.to_dict() for feature, moments in stats.items()}
                for key, stats in self.feature_stats.items()
            },
            "root_cause_counts": dict(self.root_cause_counts),
            "root_cause_centroids": {
                cause: {feature: moments.to_dict() for feature, moments in stats.items()}
                for cause, stats in self.root_cause_centroids.items()
            },
        }

    @classmethod
    def load(cls, path: Path) -> "OnlineSelfLearningModel":
        data = json.loads(path.read_text(encoding="utf-8"))
        model = cls(warmup=int(data.get("warmup", 24)), anomaly_z=float(data.get("anomaly_z", 2.7)))
        model.feature_stats.clear()
        for key, stats in dict(data.get("feature_stats", {})).items():
            loaded = {feature: OnlineMoments.from_dict(value) for feature, value in dict(stats).items()}
            model.feature_stats[key] = {feature: loaded.get(feature, OnlineMoments()) for feature in FEATURES}
        model.root_cause_counts = Counter(dict(data.get("root_cause_counts", {})))
        model.root_cause_centroids.clear()
        for cause, stats in dict(data.get("root_cause_centroids", {})).items():
            loaded = {feature: OnlineMoments.from_dict(value) for feature, value in dict(stats).items()}
            model.root_cause_centroids[cause] = {feature: loaded.get(feature, OnlineMoments()) for feature in FEATURES}
        return model

    def _predict_root_cause(self, features: dict[str, float]) -> tuple[str, float]:
        if not self.root_cause_counts:
            return "unknown", 0.0

        heuristic_cause, heuristic_confidence = self._heuristic_root_cause(features)
        if heuristic_cause != "unknown":
            return heuristic_cause, heuristic_confidence

        scored: list[tuple[float, str]] = []
        for cause, stats in self.root_cause_centroids.items():
            if self.root_cause_counts[cause] < 3:
                continue
            distance = 0.0
            used = 0
            for feature, value in features.items():
                moments = stats.get(feature, OnlineMoments())
                if moments.count < 2:
                    continue
                scale = max(0.1, moments.std)
                distance += ((value - moments.mean) / scale) ** 2
                used += 1
            if used:
                scored.append((math.sqrt(distance / used), cause))

        if not scored:
            return "unknown", 0.0
        scored.sort(key=lambda item: item[0])
        best_distance, best_cause = scored[0]
        confidence = 1.0 / (1.0 + best_distance)
        return best_cause, confidence

    def _heuristic_root_cause(self, features: dict[str, float]) -> tuple[str, float]:
        """Fast RCA guardrails for KPM regimes with clear physical meaning."""
        latency = features["latency_ms"]
        loss = features["packet_loss_pct"]
        prb = features["prb_util_pct"]
        sinr = features["sinr_db"]
        bler = features["bler_pct"]
        harq = features["harq_retx_pct"]
        cqi = features["cqi"]
        rlc_buffer = features["rlc_buffer_kbytes"]
        scheduler_delay = features["mac_scheduler_delay_ms"]
        timing_offset = features["timing_offset_us"]
        fronthaul_delay = features["fronthaul_delay_ms"]
        rsrp = features["rsrp_dbm"]
        rsrq = features["rsrq_db"]
        evm = features["evm_pct"]
        interference_power = features["interference_power_dbm"]
        beam_misalignment = features["beam_misalignment_deg"]
        antenna_vswr = features["antenna_vswr"]
        rf_temperature = features["rf_temperature_c"]
        rrc_setup_fail = features["rrc_setup_fail_pct"]
        rrc_reestab = features["rrc_reestab_rate_pct"]
        pdcp_discard = features["pdcp_discard_rate_pct"]
        pdcp_reorder = features["pdcp_reordering_delay_ms"]
        sdap_drop = features["sdap_qos_flow_drop_pct"]
        qfi_violation = features["qfi_violation_pct"]
        session_drop = features["session_drop_rate_pct"]
        mobility_pingpong = features["mobility_pingpong_pct"]
        amf_fail = features["amf_registration_fail_pct"]
        amf_paging = features["amf_paging_delay_ms"]
        pdu_setup = features["pdu_session_setup_ms"]
        pdu_fail = features["pdu_session_fail_pct"]
        upf_cpu = features["upf_cpu_util_pct"]
        upf_drop = features["upf_packet_drop_pct"]
        gtp_loss = features["gtp_tunnel_loss_pct"]
        n3_rtt = features["n3_rtt_ms"]
        n6_rtt = features["n6_internet_rtt_ms"]
        transport_jitter = features["transport_jitter_ms"]

        if self.root_cause_counts.get("cell_congestion", 0) >= 3 and (
            (prb >= 88 and latency >= 50) or (prb >= 82 and rlc_buffer >= 1250 and scheduler_delay >= 11)
        ):
            return "cell_congestion", 0.86
        if self.root_cause_counts.get("radio_link_degradation", 0) >= 3 and (
            (sinr <= 5 and (loss >= 5 or bler >= 5)) or (sinr <= 9 and cqi <= 5.5 and harq >= 12)
        ):
            return "radio_link_degradation", 0.84
        if self.root_cause_counts.get("spectrum_interference", 0) >= 3 and (
            (interference_power >= -78 and rsrq <= -15 and evm >= 8)
            or (beam_misalignment >= 18 and rsrp <= -105 and bler >= 3.5)
        ):
            return "spectrum_interference", 0.86
        if self.root_cause_counts.get("radio_quality_degradation", 0) >= 3 and (
            antenna_vswr >= 2.1 or rf_temperature >= 78 or (rsrp <= -112 and rsrq <= -16)
        ):
            return "radio_quality_degradation", 0.83
        if self.root_cause_counts.get("packet_loss_degradation", 0) >= 3 and loss >= 8 and sinr > 5:
            return "packet_loss_degradation", 0.8
        if self.root_cause_counts.get("radio_quality_degradation", 0) >= 3 and sinr <= 2 and loss < 5 and bler < 5:
            return "radio_quality_degradation", 0.82
        if self.root_cause_counts.get("timing_drift", 0) >= 3 and (
            timing_offset >= 20 and (fronthaul_delay >= 4.2 or bler >= 3.0)
        ):
            return "timing_drift", 0.82
        if self.root_cause_counts.get("handover_instability", 0) >= 3 and (
            mobility_pingpong >= 5 or rrc_reestab >= 4 or (rrc_setup_fail >= 5 and session_drop >= 2)
        ):
            return "handover_instability", 0.84
        if self.root_cause_counts.get("qos_session_degradation", 0) >= 3 and (
            sdap_drop >= 4 or qfi_violation >= 6 or (pdcp_discard >= 4 and pdcp_reorder >= 8)
        ):
            return "qos_session_degradation", 0.83
        if self.root_cause_counts.get("core_control_plane_degradation", 0) >= 3 and (
            amf_fail >= 3 or amf_paging >= 80 or pdu_fail >= 3 or pdu_setup >= 180
        ):
            return "core_control_plane_degradation", 0.84
        if self.root_cause_counts.get("upf_user_plane_congestion", 0) >= 3 and (
            upf_cpu >= 82 or upf_drop >= 3 or gtp_loss >= 2.5 or n3_rtt >= 45
        ):
            return "upf_user_plane_congestion", 0.84
        if self.root_cause_counts.get("transport_path_degradation", 0) >= 3 and (
            n6_rtt >= 90 or transport_jitter >= 18 or (n3_rtt >= 35 and gtp_loss >= 1.5)
        ):
            return "transport_path_degradation", 0.82
        return "unknown", 0.0

    def _stats_for_key(self, key: str) -> dict[str, OnlineMoments]:
        stats = self.feature_stats[key]
        for feature in FEATURES:
            stats.setdefault(feature, OnlineMoments())
        return stats

    def _centroid_for_cause(self, cause: str) -> dict[str, OnlineMoments]:
        stats = self.root_cause_centroids[cause]
        for feature in FEATURES:
            stats.setdefault(feature, OnlineMoments())
        return stats

    @staticmethod
    def _key(row: dict[str, object]) -> str:
        return f"{row.get('cell_id', 'unknown')}::{row.get('service_class', 'unknown')}"

    @staticmethod
    def _features(row: dict[str, object]) -> dict[str, float]:
        return {feature: float(row.get(feature, 0.0)) for feature in FEATURES}

    @staticmethod
    def _bool(value: object) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).lower() == "true"
