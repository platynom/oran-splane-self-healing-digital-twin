from __future__ import annotations

"""Simulator-only robustness harness for realizable PTP replay scenarios.

Candidates are expressed as protocol/scenario parameters and then regenerated
through the project's clock simulator.  The harness never edits model feature
vectors directly and never transmits packets to a network.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import yaml

from discriminator.model import train_and_evaluate
from discriminator.openset import apply_persistence
from faults.injectors import scenario_spec
from fronthaul_sim.simulator import SimConfig, simulate
from ingest import ptp_wire
from ingest.schema import coerce_telemetry
from telemetry.features import configured_feature_columns, window_features


ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_REPLAY_FIELDS = frozenset({"sequence_id", "origin_timestamp", "message_type"})
MESSAGE_CODES = {
    "Sync": ptp_wire.MT_SYNC,
    "Follow_Up": ptp_wire.MT_FOLLOW_UP,
    "Delay_Req": ptp_wire.MT_DELAY_REQ,
    "Delay_Resp": ptp_wire.MT_DELAY_RESP,
    "Announce": ptp_wire.MT_ANNOUNCE,
}
PACKET_LENGTHS = {
    "Sync": 58.0,
    "Follow_Up": 58.0,
    "Delay_Req": 58.0,
    "Delay_Resp": 58.0,
    "Announce": 78.0,
}


@dataclass(frozen=True)
class ReplayParameters:
    """Problem-space controls for a replayed PTP packet sequence."""

    magnitude_ns: float
    injection_cadence_s: float
    forged_fields: tuple[str, ...] = ("sequence_id", "origin_timestamp")
    ramp_rate_ns_per_s: float = 0.0
    onset_s: float = 2.0
    duration_s: float = 3.0
    replay_depth: int = 2
    seed: int = 1588

    def validate(self, dt_s: float) -> None:
        unknown = set(self.forged_fields) - SUPPORTED_REPLAY_FIELDS
        if unknown:
            raise ValueError(f"unsupported replay fields: {sorted(unknown)}")
        if not self.forged_fields:
            raise ValueError("at least one PTP field must be forged")
        if self.magnitude_ns < 0 or self.ramp_rate_ns_per_s < 0:
            raise ValueError("magnitude and ramp rate must be non-negative")
        if self.injection_cadence_s < dt_s:
            raise ValueError("injection cadence cannot be faster than simulator cadence")
        if self.onset_s < 0 or self.duration_s <= 0:
            raise ValueError("onset must be non-negative and duration must be positive")
        if not 1 <= self.replay_depth <= 65535:
            raise ValueError("replay_depth must fit a PTP sequence ID")

    def to_json(self) -> str:
        payload = asdict(self)
        payload["forged_fields"] = list(self.forged_fields)
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class CandidateResult:
    params: str
    exceeds_budget: bool
    offset_ns: float
    transformer_flagged: bool
    rf_flagged: bool
    openset_flagged: bool


def load_config(path: Path | None = None) -> dict:
    with (path or ROOT / "config" / "default.yaml").open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def sim_config(config: dict, seed: int) -> SimConfig:
    sim = config["sim"]
    oscillator = config.get("oscillator", {})
    sources = config.get("time_sources", {})
    return SimConfig(
        seed=seed,
        dt_s=float(sim["dt_s"]),
        duration_s=float(sim["duration_s"]),
        noise_ns=float(sim["noise_ns"]),
        base_delay_ns=float(sim["base_delay_ns"]),
        servo_gain=float(sim["servo_gain"]),
        synce_gain=float(sim["synce_gain"]),
        drift_ppb=float(sim["drift_ppb"]),
        holdover_nominal_drift_ppb=float(oscillator.get("holdover_nominal_drift_ppb", 6.0)),
        holdover_tolerance_ppb=float(oscillator.get("holdover_tolerance_ppb", 2.0)),
        disciplined_tolerance_ppb=float(oscillator.get("disciplined_tolerance_ppb", 1.5)),
        source_agreement_tolerance_ns=float(sources.get("source_agreement_tolerance_ns", 20.0)),
        gnss_reference_noise_ns=float(sources.get("gnss_reference_noise_ns", 2.5)),
        ptp_reference_noise_ns=float(sources.get("ptp_reference_noise_ns", 6.0)),
        peer_reference_noise_ns=float(sources.get("peer_reference_noise_ns", 4.0)),
        gnss_reference_drift_ppb=float(sources.get("gnss_reference_drift_ppb", 0.05)),
        ptp_reference_drift_ppb=float(sources.get("ptp_reference_drift_ppb", 0.12)),
        peer_reference_drift_ppb=float(sources.get("peer_reference_drift_ppb", 0.08)),
        time_error_budget_ns=float(config["time_error_budget_ns"]),
    )


def _injection_indices(params: ReplayParameters, cfg: SimConfig) -> set[int]:
    count = int(np.floor(params.duration_s / params.injection_cadence_s)) + 1
    times = params.onset_s + np.arange(count) * params.injection_cadence_s
    return {int(round(float(value) / cfg.dt_s)) for value in times if value <= params.onset_s + params.duration_s}


def _validate_wire_encoding(row: dict, params: ReplayParameters) -> None:
    """Round-trip each forged packet through the existing PTP codec."""
    name = str(row["ptp_msg_type"])
    message_type = MESSAGE_CODES[name]
    origin = int(round((float(row["t_s"]) * 1e9) - float(row["offset_ns"])))
    payload = ptp_wire.build_ptp_payload(
        message_type,
        int(row["ptp_seq_id"]),
        origin_ts_ns=max(0, origin),
    )
    decoded = ptp_wire.decode_ptp_payload(payload)
    if decoded is None or decoded.msg_type != message_type:
        raise ValueError("candidate did not round-trip as a legal PTP payload")
    if "sequence_id" in params.forged_fields and decoded.seq_id != int(row["ptp_seq_id"]) % 65536:
        raise ValueError("replayed sequence ID did not survive PTP encoding")


def generate_replay_telemetry(params: ReplayParameters, config: dict | None = None) -> pd.DataFrame:
    """Regenerate one parameterized replay scenario through the existing simulator."""
    cfg_dict = config or load_config()
    cfg = sim_config(cfg_dict, params.seed)
    params.validate(cfg.dt_s)
    spec = scenario_spec("ptp_replay")
    if spec.label != "H1":
        raise ValueError("ptp_replay must remain an H1 scenario")
    injection_indices = _injection_indices(params, cfg)

    def mutate(row: dict, index: int, _rng: np.random.Generator) -> None:
        t_s = float(row["t_s"])
        active = params.onset_s <= t_s <= params.onset_s + params.duration_s
        if not active:
            return
        row["attack_flag"] = True
        row["attack_family"] = "replay"
        if index not in injection_indices:
            return
        elapsed = t_s - params.onset_s
        magnitude = params.magnitude_ns + params.ramp_rate_ns_per_s * elapsed
        if "sequence_id" in params.forged_fields:
            row["ptp_seq_id"] = (int(row["ptp_seq_id"]) - params.replay_depth) % 65536
        if "origin_timestamp" in params.forged_fields:
            row["offset_ns"] = float(row["offset_ns"]) + magnitude
            row["measured_offset_ns"] = float(row["measured_offset_ns"]) + magnitude
        if "message_type" in params.forged_fields:
            row["ptp_msg_type"] = "Follow_Up"
        _validate_wire_encoding(row, params)

    telemetry = simulate(cfg, scenario="ptp_replay", mutator=mutate)
    telemetry["run_id"] = 0
    telemetry["label"] = np.where(telemetry["attack_flag"], "H1", "healthy")
    return coerce_telemetry(telemetry)


def telemetry_packet_features(telemetry: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Map simulated legal PTP rows to the Phase-0 packet victim's five inputs."""
    messages = telemetry["ptp_msg_type"].astype(str)
    unknown = sorted(set(messages) - set(MESSAGE_CODES))
    if unknown:
        raise ValueError(f"unsupported PTP message types: {unknown}")
    inter_arrival = telemetry["t_s"].astype(float).diff().fillna(0.0).clip(lower=0.0)
    features = np.column_stack(
        [
            np.zeros(len(telemetry), dtype=float),
            messages.map(PACKET_LENGTHS).to_numpy(dtype=float),
            telemetry["ptp_seq_id"].to_numpy(dtype=float) % 65536,
            messages.map(MESSAGE_CODES).to_numpy(dtype=float),
            inter_arrival.to_numpy(dtype=float),
        ]
    ).astype(np.float32)
    labels = telemetry["attack_flag"].astype(int).to_numpy(dtype=np.int64)
    return features, labels


class RobustnessHarness:
    """Score replay candidates against frozen project and Phase-0 victims."""

    def __init__(self, root: Path = ROOT, config: dict | None = None) -> None:
        self.root = root
        self.config = config or load_config(root / "config" / "default.yaml")
        self.feature_columns = configured_feature_columns(self.config)
        training_windows = pd.read_csv(root / "dataset" / "splane_windows.csv")
        # Reuse the Phase-0 adapter's untracked metrics directory. The protected
        # training API requires an output path even though this harness consumes
        # only the fitted estimator.
        api_out = root / "results" / "evasion" / "project_api"
        self.rf, _metrics = train_and_evaluate(training_windows, self.config, api_out)
        self.transformer = self._load_transformer(root / "results" / "evasion" / "victim_transformer.pt")

    @staticmethod
    def _load_transformer(path: Path):
        import torch

        from evasion.victim_transformer import PacketTransformer, TransformerVictim

        try:
            checkpoint = torch.load(path, map_location="cpu", weights_only=False)
        except TypeError:  # PyTorch versions before weights_only was introduced.
            checkpoint = torch.load(path, map_location="cpu")
        model = PacketTransformer(sequence_length=int(checkpoint["window_size"]))
        model.load_state_dict(checkpoint["state_dict"])
        model.eval()
        return TransformerVictim(
            model=model,
            feature_mean=np.asarray(checkpoint["feature_mean"]),
            feature_std=np.asarray(checkpoint["feature_std"]),
            train_sessions=tuple(checkpoint["train_sessions"]),
            test_sessions=tuple(checkpoint["test_sessions"]),
            training_loss=list(checkpoint["training_loss"]),
        )

    def _transformer_flag(self, telemetry: pd.DataFrame) -> bool:
        import torch

        from evasion.victim_transformer import sliding_windows

        packet_features, packet_labels = telemetry_packet_features(telemetry)
        windows, attack_overlap = sliding_windows(
            self.transformer.transform(packet_features), packet_labels
        )
        with torch.no_grad():
            probabilities = torch.sigmoid(self.transformer.model(torch.from_numpy(windows))).numpy()
        attack_predictions = probabilities[attack_overlap.astype(bool)] >= 0.5
        return bool(attack_predictions.any())

    def evaluate(self, params: ReplayParameters) -> CandidateResult:
        telemetry = generate_replay_telemetry(params, self.config)
        dataset = self.config["dataset"]
        windows = window_features(
            telemetry,
            window_s=float(dataset["window_s"]),
            step_s=float(dataset["step_s"]),
        )
        attack_windows = windows[windows["label"] == "H1"].copy()
        if attack_windows.empty:
            raise ValueError("candidate produced no attack windows")
        offset_ns = float(attack_windows["offset_abs_max"].max())
        matrix = attack_windows[self.feature_columns]
        raw_rf = self.rf.predict(matrix) == "H1"
        raw_novel = self.rf.novelty_detector_.predict_novel(matrix)
        persistence = self.config["openset"]["persistence"]
        n, m = int(persistence["n"]), int(persistence["m"])
        rf_flags = apply_persistence(raw_rf, n=n, m=m)
        novelty_flags = apply_persistence(raw_novel, n=n, m=m)
        return CandidateResult(
            params=params.to_json(),
            exceeds_budget=bool(offset_ns >= float(self.config["time_error_budget_ns"])),
            offset_ns=offset_ns,
            transformer_flagged=self._transformer_flag(telemetry),
            rf_flagged=bool(rf_flags.any()),
            openset_flagged=bool(novelty_flags.any()),
        )

    def sweep(self, candidates: Iterable[ReplayParameters]) -> pd.DataFrame:
        rows = [asdict(self.evaluate(candidate)) for candidate in candidates]
        return pd.DataFrame(
            rows,
            columns=[
                "params",
                "exceeds_budget",
                "offset_ns",
                "transformer_flagged",
                "rf_flagged",
                "openset_flagged",
            ],
        )
