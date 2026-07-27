from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .config import Paths


class DecisionStore:
    """Small SQLite store for local incidents, runs, and live decisions."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Paths.outputs / "oran_twin.sqlite"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _init(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    run_name TEXT,
                    mode TEXT,
                    cell_id TEXT,
                    service_class TEXT,
                    fault_type TEXT,
                    root_cause TEXT,
                    healing_action TEXT,
                    risk_score REAL,
                    automation_safety_score REAL,
                    automation_safety_decision TEXT,
                    unsafe_action_prevented INTEGER,
                    payload_json TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS run_summaries (
                    run_name TEXT PRIMARY KEY,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    records INTEGER,
                    summary_json TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS feature_rows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    source TEXT,
                    cell_id TEXT,
                    service_class TEXT,
                    feature_json TEXT,
                    label_json TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS data_quality_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    source TEXT,
                    severity TEXT,
                    event_type TEXT,
                    message TEXT,
                    payload_json TEXT
                )
                """
            )

    def record_decision(self, *, run_name: str, mode: str, decision: dict[str, Any]) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                INSERT INTO decisions (
                    run_name, mode, cell_id, service_class, fault_type, root_cause,
                    healing_action, risk_score, automation_safety_score,
                    automation_safety_decision, unsafe_action_prevented, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_name,
                    mode,
                    str(decision.get("cell_id", "")),
                    str(decision.get("service_class", "")),
                    str(decision.get("fault_type", "")),
                    str(decision.get("root_cause", "")),
                    str(decision.get("healing_action", "")),
                    float(decision.get("twin_risk_score", 0.0)),
                    float(decision.get("automation_safety_score", 0.0)),
                    str(decision.get("automation_safety_decision", "")),
                    int(bool(decision.get("unsafe_action_prevented", False))),
                    json.dumps(decision, default=str, separators=(",", ":")),
                ),
            )

    def record_summary(self, *, run_name: str, records: int, summary: dict[str, Any]) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO run_summaries (run_name, records, summary_json)
                VALUES (?, ?, ?)
                """,
                (run_name, records, json.dumps(summary, default=str, separators=(",", ":"))),
            )

    def record_feature_row(
        self,
        *,
        source: str,
        row: dict[str, Any],
        label: dict[str, Any] | None = None,
    ) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                INSERT INTO feature_rows (source, cell_id, service_class, feature_json, label_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    source,
                    str(row.get("cell_id", "")),
                    str(row.get("service_class", "")),
                    json.dumps(row, default=str, separators=(",", ":")),
                    json.dumps(label or {}, default=str, separators=(",", ":")),
                ),
            )

    def record_data_quality_event(
        self,
        *,
        source: str,
        severity: str,
        event_type: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                INSERT INTO data_quality_events (source, severity, event_type, message, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    source,
                    severity,
                    event_type,
                    message,
                    json.dumps(payload or {}, default=str, separators=(",", ":")),
                ),
            )

    def live_counts(self, *, run_name: str = "live_oai_stream") -> dict[str, Any]:
        with sqlite3.connect(self.path) as conn:
            decisions = int(conn.execute("SELECT COUNT(*) FROM decisions WHERE run_name = ?", (run_name,)).fetchone()[0])
            features = int(conn.execute("SELECT COUNT(*) FROM feature_rows WHERE source = ?", ("live_oai_metrics",)).fetchone()[0])
            quality_events = int(conn.execute("SELECT COUNT(*) FROM data_quality_events").fetchone()[0])
            recent = conn.execute(
                """
                SELECT created_at, cell_id, service_class, root_cause, healing_action,
                       risk_score, automation_safety_decision, unsafe_action_prevented
                FROM decisions
                WHERE run_name = ?
                ORDER BY id DESC
                LIMIT 10
                """,
                (run_name,),
            ).fetchall()
        return {
            "database": str(self.path),
            "decisions": decisions,
            "feature_rows": features,
            "data_quality_events": quality_events,
            "recent_decisions": [
                {
                    "created_at": item[0],
                    "cell_id": item[1],
                    "service_class": item[2],
                    "root_cause": item[3],
                    "healing_action": item[4],
                    "risk_score": item[5],
                    "automation_safety_decision": item[6],
                    "unsafe_action_prevented": bool(item[7]),
                }
                for item in recent
            ],
        }
