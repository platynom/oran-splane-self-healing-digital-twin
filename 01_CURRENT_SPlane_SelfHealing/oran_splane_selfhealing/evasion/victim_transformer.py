from __future__ import annotations

"""Leakage-resistant TIMESAFE-class packet-sequence victim reproduction.

The public packet labels are aligned against their original pcap records before
training. Complete capture sessions, rather than overlapping windows, are assigned
to train or test. This deliberately fixes the released implementation's
window-level split leakage while retaining its two-layer Transformer design.
"""

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import GroupShuffleSplit
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from discriminator.model import train_and_evaluate
from discriminator.openset import apply_persistence
from ingest import ptp_wire
from ingest.schema import coerce_telemetry
from telemetry.features import configured_feature_columns, window_features


ROOT = Path(__file__).resolve().parents[1]
FEATURE_NAMES = (
    "direction",
    "packet_length",
    "sequence_id",
    "message_type",
    "inter_arrival_s",
)
WINDOW_SIZE = 40
WINDOW_STRIDE = 2
GATE_THRESHOLD = 0.95

# Each label stream was produced from the named public pcap. Announce sessions 1
# and 2 are separate released capture files whose packet streams happen to match,
# but their attack intervals differ and remain grouped by their declared session.
SESSION_SOURCES = {
    "announce_session_1": ("15min_announce_attack.pcap", "announce"),
    "announce_session_2": ("2024-10-06-announce_attack_UEdata.pcap", "announce"),
    "announce_session_3": ("2024-10-08-announce_attack 1.pcap", "announce"),
    "sync_followup_session": ("2024-10-08-sync_attack 1.pcap", "sync_follow_up"),
    "sync_singlestep_session": (
        "2024-10-08-sync_attack_singlestep 1.pcap",
        "sync_single_step",
    ),
}


@dataclass(frozen=True)
class CaptureSession:
    capture_id: str
    attack_family: str
    packet_features: np.ndarray
    packet_labels: np.ndarray
    pcap_path: Path


@dataclass
class TransformerVictim:
    model: "PacketTransformer"
    feature_mean: np.ndarray
    feature_std: np.ndarray
    train_sessions: tuple[str, ...]
    test_sessions: tuple[str, ...]
    training_loss: list[float]

    def transform(self, values: np.ndarray) -> np.ndarray:
        prepared = prepare_packet_features(values)
        return ((prepared - self.feature_mean) / self.feature_std).astype(np.float32)


class PacketTransformer(nn.Module):
    """Small two-layer encoder over fixed-length PTP packet sequences."""

    def __init__(
        self,
        num_features: int = len(FEATURE_NAMES),
        sequence_length: int = WINDOW_SIZE,
        model_dim: int = 32,
        heads: int = 4,
        layers: int = 2,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.sequence_length = int(sequence_length)
        self.input_projection = nn.Linear(num_features, model_dim)
        self.class_token = nn.Parameter(torch.zeros(1, 1, model_dim))
        self.position = nn.Parameter(torch.zeros(1, self.sequence_length + 1, model_dim))
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=model_dim,
            nhead=heads,
            dim_feedforward=model_dim * 2,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=False,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=layers)
        self.output = nn.Sequential(nn.LayerNorm(model_dim), nn.Linear(model_dim, 1))
        nn.init.normal_(self.class_token, std=0.02)
        nn.init.normal_(self.position, std=0.02)

    def forward(self, packets: torch.Tensor) -> torch.Tensor:
        if packets.ndim != 3 or packets.shape[1] != self.sequence_length:
            raise ValueError(
                f"expected [batch, {self.sequence_length}, features], got {tuple(packets.shape)}"
            )
        encoded = self.input_projection(packets)
        cls = self.class_token.expand(encoded.shape[0], -1, -1)
        encoded = torch.cat((cls, encoded), dim=1) + self.position
        return self.output(self.encoder(encoded)[:, 0]).squeeze(-1)


def _pcap_packet_frame(path: Path) -> pd.DataFrame:
    """Read the five specified packet features directly from a public pcap."""
    rows: list[dict[str, float]] = []
    source_codes: dict[bytes, int] = {}
    previous_ns: int | None = None
    for capture_ns, frame in ptp_wire.read_pcap(str(path)):
        payload = ptp_wire.parse_eth_frame(frame)
        if payload is None:
            continue
        message = ptp_wire.decode_ptp_payload(payload)
        if message is None:
            continue
        source = frame[6:12]
        direction = source_codes.setdefault(source, len(source_codes))
        inter_arrival = 0.0 if previous_ns is None else (capture_ns - previous_ns) / 1e9
        previous_ns = capture_ns
        rows.append(
            {
                "direction": float(direction),
                "packet_length": float(len(frame)),
                "sequence_id": float(message.seq_id),
                "message_type": float(message.msg_type),
                "inter_arrival_s": float(max(inter_arrival, 0.0)),
            }
        )
    if not rows:
        raise ValueError(f"no decodable PTP packets in {path}")
    return pd.DataFrame(rows, columns=FEATURE_NAMES)


def _validate_operational_sessions(root: Path, capture_id: str, packet_count: int) -> None:
    paths = sorted((root / "data" / "external" / "timesafe_sessions").glob(f"{capture_id}__*.csv"))
    if len(paths) != 2:
        raise ValueError(f"{capture_id}: expected benign and attack operational session CSVs")
    rows = sum(len(pd.read_csv(path)) for path in paths)
    # The offset ingester can omit the first PTP packet while waiting for a Sync.
    if abs(rows - packet_count) > 1:
        raise ValueError(
            f"{capture_id}: operational rows={rows} do not align with packet labels={packet_count}"
        )


def load_capture_sessions(root: Path = ROOT) -> list[CaptureSession]:
    """Load labels, verify their pcap alignment, and validate operational CSVs."""
    label_root = root / "data" / "external" / "timesafe_multi_raw"
    pcap_root = root / "data" / "external" / "s-plane_security_repo" / "DataCollectionPTP"
    sessions: list[CaptureSession] = []
    for capture_id, (pcap_name, family) in SESSION_SOURCES.items():
        label_path = label_root / f"{capture_id}_labels.csv"
        pcap_path = pcap_root / pcap_name
        if not label_path.exists() or not pcap_path.exists():
            raise FileNotFoundError(f"missing public source for {capture_id}")
        labels = pd.read_csv(label_path)
        required = {"Source", "Length", "SequenceID", "MessageType", "Time Interval", "Label"}
        if not required.issubset(labels.columns):
            raise ValueError(f"{label_path} lacks columns: {sorted(required - set(labels.columns))}")
        packets = _pcap_packet_frame(pcap_path)
        if len(packets) != len(labels):
            raise ValueError(f"{capture_id}: pcap packets={len(packets)}, labels={len(labels)}")
        checks = {
            "direction": labels["Source"].to_numpy(dtype=float),
            "packet_length": labels["Length"].to_numpy(dtype=float),
            "sequence_id": labels["SequenceID"].to_numpy(dtype=float),
            "message_type": labels["MessageType"].to_numpy(dtype=float),
            "inter_arrival_s": labels["Time Interval"].to_numpy(dtype=float),
        }
        for name, expected in checks.items():
            actual = packets[name].to_numpy(dtype=float)
            if not np.allclose(actual, expected, rtol=1e-5, atol=1e-6):
                raise ValueError(f"{capture_id}: pcap/{name} does not align with released labels")
        packet_labels = labels["Label"].to_numpy(dtype=np.int64)
        if set(np.unique(packet_labels)) != {0, 1}:
            raise ValueError(f"{capture_id}: both benign and attack packets are required")
        _validate_operational_sessions(root, capture_id, len(labels))
        sessions.append(
            CaptureSession(
                capture_id=capture_id,
                attack_family=family,
                packet_features=packets.to_numpy(dtype=np.float32),
                packet_labels=packet_labels,
                pcap_path=pcap_path,
            )
        )
    return sessions


def session_holdout(
    sessions: Iterable[CaptureSession], seed: int = 1588, test_size: float = 0.4
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    """Choose a complete-session split with Announce and Sync on both sides."""
    items = list(sessions)
    capture_ids = np.asarray([item.capture_id for item in items])
    coarse_family = np.asarray(
        ["announce" if item.attack_family == "announce" else "sync" for item in items]
    )
    splitter = GroupShuffleSplit(n_splits=64, test_size=test_size, random_state=seed)
    for split_index, (train_index, test_index) in enumerate(
        splitter.split(np.zeros((len(items), 1)), coarse_family, capture_ids)
    ):
        if set(coarse_family[train_index]) == set(coarse_family[test_index]) == {"announce", "sync"}:
            return (
                tuple(capture_ids[train_index]),
                tuple(capture_ids[test_index]),
                split_index,
            )
    raise ValueError("could not form a family-covered complete-session split")


def prepare_packet_features(values: np.ndarray) -> np.ndarray:
    """Apply a fixed heavy-tail transform to inter-arrival time before scaling."""
    prepared = np.asarray(values, dtype=np.float64).copy()
    if prepared.ndim != 2 or prepared.shape[1] != len(FEATURE_NAMES):
        raise ValueError(f"expected packet matrix with {len(FEATURE_NAMES)} columns")
    prepared[:, FEATURE_NAMES.index("inter_arrival_s")] = np.log1p(
        np.clip(prepared[:, FEATURE_NAMES.index("inter_arrival_s")], 0.0, None) * 1e6
    )
    return prepared


def sliding_windows(
    features: np.ndarray,
    labels: np.ndarray,
    window_size: int = WINDOW_SIZE,
    stride: int = WINDOW_STRIDE,
) -> tuple[np.ndarray, np.ndarray]:
    """Build fixed packet windows; any injected packet makes the window attack."""
    if window_size < 2 or stride < 1:
        raise ValueError("window_size must be >=2 and stride must be >=1")
    if len(features) != len(labels):
        raise ValueError("packet features and labels must have equal length")
    starts = np.arange(0, len(features) - window_size + 1, stride, dtype=int)
    if not len(starts):
        raise ValueError("capture is shorter than one packet window")
    windows = np.stack([features[start : start + window_size] for start in starts]).astype(np.float32)
    targets = np.asarray(
        [int(np.any(labels[start : start + window_size])) for start in starts],
        dtype=np.int64,
    )
    return windows, targets


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)


def train_transformer_victim(
    sessions: list[CaptureSession],
    train_ids: tuple[str, ...],
    test_ids: tuple[str, ...],
    *,
    seed: int = 1588,
    epochs: int = 6,
    batch_size: int = 512,
    max_windows_per_session: int = 12_000,
) -> TransformerVictim:
    """Train the fixed two-layer model on complete training captures, CPU-only."""
    _seed_everything(seed)
    torch.set_num_threads(max(1, min(8, torch.get_num_threads())))
    by_id = {item.capture_id: item for item in sessions}
    prepared_train = [prepare_packet_features(by_id[name].packet_features) for name in train_ids]
    feature_rows = np.concatenate(prepared_train, axis=0)
    mean = feature_rows.mean(axis=0)
    std = feature_rows.std(axis=0)
    std[std < 1e-9] = 1.0

    window_frames: list[np.ndarray] = []
    window_labels: list[np.ndarray] = []
    rng = np.random.default_rng(seed)
    for capture_id in train_ids:
        item = by_id[capture_id]
        normalized = ((prepare_packet_features(item.packet_features) - mean) / std).astype(np.float32)
        windows, labels = sliding_windows(normalized, item.packet_labels)
        if len(windows) > max_windows_per_session:
            chosen = np.sort(rng.choice(len(windows), max_windows_per_session, replace=False))
            windows, labels = windows[chosen], labels[chosen]
        window_frames.append(windows)
        window_labels.append(labels)
    X_train = np.concatenate(window_frames, axis=0)
    y_train = np.concatenate(window_labels, axis=0)
    generator = torch.Generator().manual_seed(seed)
    loader = DataLoader(
        TensorDataset(torch.from_numpy(X_train), torch.from_numpy(y_train.astype(np.float32))),
        batch_size=batch_size,
        shuffle=True,
        generator=generator,
        num_workers=0,
    )
    model = PacketTransformer()
    positives = int(y_train.sum())
    negatives = int(len(y_train) - positives)
    loss_fn = nn.BCEWithLogitsLoss(
        pos_weight=torch.tensor([negatives / max(positives, 1)], dtype=torch.float32)
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    losses: list[float] = []
    model.train()
    for _epoch in range(epochs):
        total_loss = 0.0
        total_rows = 0
        for packets, targets in loader:
            optimizer.zero_grad(set_to_none=True)
            logits = model(packets)
            loss = loss_fn(logits, targets)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += float(loss.detach()) * len(targets)
            total_rows += len(targets)
        losses.append(total_loss / max(total_rows, 1))
    return TransformerVictim(
        model=model.eval(),
        feature_mean=mean,
        feature_std=std,
        train_sessions=train_ids,
        test_sessions=test_ids,
        training_loss=losses,
    )


def _metric_row(
    victim: str,
    source: str,
    truth: np.ndarray,
    prediction: np.ndarray,
    train_ids: tuple[str, ...],
    test_ids: tuple[str, ...],
) -> dict[str, object]:
    matrix = confusion_matrix(truth, prediction, labels=[0, 1])
    tn, fp, fn, tp = (int(value) for value in matrix.ravel())
    accuracy = float(accuracy_score(truth, prediction))
    return {
        "victim": victim,
        "data_source": source,
        "split_strategy": "GroupShuffleSplit_complete_capture",
        "train_sessions": ";".join(train_ids),
        "test_sessions": ";".join(test_ids),
        "test_samples": int(len(truth)),
        "accuracy": accuracy,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
        "confusion_matrix": json.dumps(matrix.tolist(), separators=(",", ":")),
        "gate_threshold": GATE_THRESHOLD if victim == "timesafe_class_transformer" else math.nan,
        "gate_passed": bool(accuracy >= GATE_THRESHOLD)
        if victim == "timesafe_class_transformer"
        else "not_applicable",
    }


@torch.no_grad()
def evaluate_transformer_victim(
    victim: TransformerVictim, sessions: list[CaptureSession], batch_size: int = 1024
) -> tuple[dict[str, object], pd.DataFrame]:
    truth_parts: list[np.ndarray] = []
    prediction_parts: list[np.ndarray] = []
    family_rows: list[dict[str, object]] = []
    by_id = {item.capture_id: item for item in sessions}
    for capture_id in victim.test_sessions:
        item = by_id[capture_id]
        windows, truth = sliding_windows(victim.transform(item.packet_features), item.packet_labels)
        logits: list[np.ndarray] = []
        for start in range(0, len(windows), batch_size):
            batch = torch.from_numpy(windows[start : start + batch_size])
            logits.append(victim.model(batch).cpu().numpy())
        prediction = (1.0 / (1.0 + np.exp(-np.concatenate(logits))) >= 0.5).astype(int)
        truth_parts.append(truth)
        prediction_parts.append(prediction)
        matrix = confusion_matrix(truth, prediction, labels=[0, 1])
        family_rows.append(
            {
                "capture_id": capture_id,
                "attack_family": item.attack_family,
                "windows": len(truth),
                "accuracy": accuracy_score(truth, prediction),
                "confusion_matrix": json.dumps(matrix.tolist(), separators=(",", ":")),
            }
        )
    truth_all = np.concatenate(truth_parts)
    prediction_all = np.concatenate(prediction_parts)
    return (
        _metric_row(
            "timesafe_class_transformer",
            "real_public_pcap_packet_windows",
            truth_all,
            prediction_all,
            victim.train_sessions,
            victim.test_sessions,
        ),
        pd.DataFrame(family_rows),
    )


def _load_project_windows(root: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in sorted((root / "data" / "external" / "timesafe_sessions").glob("*.csv")):
        telemetry = coerce_telemetry(pd.read_csv(path))
        capture_id = str(pd.read_csv(path, nrows=1)["capture_id"].iloc[0])
        windows = window_features(telemetry, window_s=0.4, step_s=0.2)
        windows["capture_id"] = capture_id
        windows["source_path"] = str(path)
        frames.append(windows)
    if not frames:
        raise ValueError("no TIMESAFE operational session CSVs found")
    return pd.concat(frames, ignore_index=True)


def evaluate_project_victim(
    root: Path,
    train_ids: tuple[str, ...],
    test_ids: tuple[str, ...],
) -> dict[str, object]:
    """Invoke the existing RF + open-set API, then apply shipped 2-of-3 persistence."""
    import yaml

    with (root / "config" / "default.yaml").open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    windows = _load_project_windows(root)
    train = windows[windows["capture_id"].isin(train_ids)].copy()
    test = windows[windows["capture_id"].isin(test_ids)].copy()
    if train["label"].nunique() != 2 or test["label"].nunique() != 2:
        raise ValueError("project victim requires H0 and H1 windows in train and test")
    # The operational ingester yields only one pre-attack window in each of the
    # first two Announce captures. The existing API stratifies on label+scenario,
    # for which a singleton is mathematically unsplittable. Exclude only those
    # two training fragments; the complete held sessions remain untouched.
    stratum = train["label"].astype(str) + "_" + train["scenario"].astype(str)
    usable = stratum.map(stratum.value_counts()) >= 2
    api_train = train[usable].copy()
    api_out = root / "results" / "evasion" / "project_api"
    classifier, _ = train_and_evaluate(api_train, config, api_out)
    columns = configured_feature_columns(config)
    raw_prediction = classifier.predict(test[columns]) == "H1"
    novelty = classifier.novelty_detector_.predict_novel(test[columns])
    protective = raw_prediction | novelty
    persisted = np.zeros(len(test), dtype=bool)
    for _capture_id, indices in test.groupby("capture_id", sort=True).groups.items():
        ordered = test.loc[indices].sort_values("window_start_s").index
        positions = test.index.get_indexer(ordered)
        persisted[positions] = apply_persistence(protective[positions], n=2, m=3)
    truth = (test["label"].to_numpy() == "H1").astype(int)
    return _metric_row(
        "project_rf_openset_2of3",
        "real_public_timesafe_telemetry_windows",
        truth,
        persisted.astype(int),
        train_ids,
        test_ids,
    )


def save_transformer_checkpoint(victim: TransformerVictim, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "state_dict": victim.model.state_dict(),
            "feature_names": FEATURE_NAMES,
            "feature_mean": victim.feature_mean,
            "feature_std": victim.feature_std,
            "window_size": WINDOW_SIZE,
            "window_stride": WINDOW_STRIDE,
            "train_sessions": victim.train_sessions,
            "test_sessions": victim.test_sessions,
            "training_loss": victim.training_loss,
            "cpu_only_reproduction": True,
        },
        path,
    )
