"""Localize S-plane problems from the curated 2026-08-30 dataset bundle.

The analysis deliberately keeps three questions separate:

1. What changed in the observed telemetry?
2. Is the change harmful (H1) or an operational confounder (H0)?
3. Which O-RAN subsystem should an operator inspect first?

Run from the active project directory:

    python scripts/analyze_problem_localization.py
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd


SCENARIOS = {
    "ptp_spoof": {
        "change": "Forged superior Announce / grandmaster takeover",
        "status": "H1 problem",
        "location": "PTP grandmaster election (BMCA) at the O-DU/O-RU S-plane boundary",
        "signals": [
            "gm_identity_changes",
            "clock_class_improve_jump",
            "priority1_changes",
            "steps_removed_changes",
            "offset_abs_max",
        ],
        "action": "Quarantine the unexpected GM; verify Announce source and BMCA attributes.",
    },
    "ptp_replay": {
        "change": "Replayed/out-of-order Sync and Follow-Up messages",
        "status": "H1 problem",
        "location": "PTP packet stream on the Open Fronthaul transport path",
        "signals": ["seq_regressions", "msg_irregularity", "offset_step_vs_drift_ratio"],
        "action": "Block the replay source and reset/revalidate sequence continuity.",
    },
    "ptp_dos_flood": {
        "change": "PTP message-rate flood",
        "status": "H1 problem",
        "location": "S-plane ingress/transport link before the O-DU PTP stack",
        "signals": ["msg_rate_mean", "msg_rate_std", "msg_irregularity"],
        "action": "Rate-limit the offending source while preserving trusted timing traffic.",
    },
    "gnss_jam": {
        "change": "GNSS loss/jamming followed by oscillator holdover",
        "status": "H1 problem",
        "location": "GNSS receiver, antenna/RF feed, or local timing source",
        "signals": [
            "gnss_loss_rate",
            "satellites_drop_max",
            "holdover_rate",
            "holdover_entry_count",
            "holdover_spec_violation_rate",
            "drift_vs_declared_state_residual",
        ],
        "action": "Switch to a trusted clock/LLS-C source and inspect the GNSS RF chain.",
    },
    "gnss_spoof": {
        "change": "Manipulated GNSS time reference",
        "status": "H1 problem",
        "location": "GNSS time source; corroboration is required outside the receiver",
        "signals": [
            "status_behaviour_disagreement",
            "drift_vs_declared_state_residual",
            "offset_step_vs_drift_ratio",
        ],
        "action": "Cross-check with authenticated GNSS or an independent physical clock.",
    },
    "pdv_congestion": {
        "change": "Packet-delay variation / congestion",
        "status": "H0 degradation",
        "location": "Fronthaul switches, queues, link scheduling, or competing traffic",
        "signals": ["pdv_std", "path_delay_mean", "offset_abs_max"],
        "action": "Inspect queue occupancy/QoS and reroute or reprioritize timing packets.",
    },
    "traffic_burst": {
        "change": "Legitimate message-rate burst",
        "status": "H0 confounder",
        "location": "Fronthaul traffic source; not a timing attack by itself",
        "signals": ["msg_rate_mean", "msg_rate_std", "msg_irregularity"],
        "action": "Observe unless timing quality also degrades; do not auto-quarantine.",
    },
    "planned_gm_failover": {
        "change": "Authorized grandmaster re-parenting",
        "status": "H0 confounder",
        "location": "PTP BMCA/grandmaster redundancy plane",
        "signals": [
            "gm_identity_changes",
            "clock_class_changes",
            "priority1_changes",
            "steps_removed_changes",
        ],
        "action": "Validate the maintenance/failover ticket and continue monitoring.",
    },
    "synce_degrade": {
        "change": "SyncE quality-level degradation",
        "status": "H0 degradation",
        "location": "Ethernet Equipment Clock / SyncE distribution chain",
        "signals": ["synce_ql_max", "offset_abs_max"],
        "action": "Trace QL advertisements and switch to the best available EEC source.",
    },
    "gnss_loss_holdover": {
        "change": "Benign GNSS loss entering specified holdover",
        "status": "H0 degradation",
        "location": "GNSS availability/local oscillator (within declared holdover envelope)",
        "signals": [
            "gnss_loss_rate",
            "holdover_rate",
            "holdover_entry_count",
            "holdover_spec_violation_rate",
        ],
        "action": "Monitor holdover duration and drift; escalate only on envelope violation.",
    },
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fmt(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    absolute = abs(float(value))
    if absolute >= 1000:
        return f"{value:,.1f}"
    if absolute >= 10:
        return f"{value:.2f}"
    return f"{value:.3f}"


def simulation_analysis(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    windows = pd.read_csv(root / "Synthetic S-Plane" / "splane_windows.csv")
    summaries: list[dict[str, object]] = []
    changes: list[dict[str, object]] = []

    for scenario, meta in SCENARIOS.items():
        subset = windows[windows["scenario"] == scenario]
        event = subset[subset["label"] != "healthy"]
        baseline = subset[subset["label"] == "healthy"]
        if event.empty or baseline.empty:
            continue

        ranked_signals: list[tuple[str, float]] = []
        for signal in meta["signals"]:
            if signal not in windows.columns:
                continue
            base_mean = pd.to_numeric(baseline[signal], errors="coerce").mean()
            event_mean = pd.to_numeric(event[signal], errors="coerce").mean()
            base_std = pd.to_numeric(baseline[signal], errors="coerce").std()
            global_scale = pd.to_numeric(windows[signal], errors="coerce").std()
            scale = max(
                float(base_std) if pd.notna(base_std) else 0.0,
                0.1 * float(global_scale) if pd.notna(global_scale) else 0.0,
                1e-9,
            )
            effect = float((event_mean - base_mean) / scale)
            ranked_signals.append((signal, abs(effect)))
            changes.append(
                {
                    "scenario": scenario,
                    "classification": meta["status"],
                    "feature": signal,
                    "healthy_mean": base_mean,
                    "event_mean": event_mean,
                    "absolute_change": event_mean - base_mean,
                    "standardized_change": effect,
                }
            )

        ranked_signals.sort(key=lambda item: item[1], reverse=True)
        strongest = ", ".join(signal for signal, _ in ranked_signals[:3])
        summaries.append(
            {
                "scenario": scenario,
                "classification": meta["status"],
                "change": meta["change"],
                "first_location_to_inspect": meta["location"],
                "strongest_observed_signals": strongest,
                "event_windows": len(event),
                "healthy_control_windows": len(baseline),
                "operator_response": meta["action"],
            }
        )

    summary_df = pd.DataFrame(summaries)
    change_df = pd.DataFrame(changes)
    change_df["absolute_standardized_change"] = change_df["standardized_change"].abs()
    change_df = change_df.sort_values(
        ["scenario", "absolute_standardized_change"], ascending=[True, False]
    )
    return summary_df, change_df


def netem_analysis(root: Path) -> pd.DataFrame:
    data = pd.read_csv(root / "Netem" / "netem_telemetry.csv")
    rows: list[dict[str, object]] = []
    for scenario, group in data.groupby("scenario", sort=False):
        duration = max(float(group["t_s"].max() - group["t_s"].min()), 1e-9)
        rows.append(
            {
                "scenario": scenario,
                "rows": len(group),
                "duration_s": duration,
                "rows_per_s": len(group) / duration,
                "offset_abs_p95_ns": group["offset_ns"].abs().quantile(0.95),
                "offset_abs_max_ns": group["offset_ns"].abs().max(),
                "pdv_std_ns": group["pdv_ns"].std(),
                "message_rate_mean_hz": group["msg_rate_hz"].mean(),
                "valid_fraction": group["telemetry_valid"].astype(str).str.lower().eq("true").mean(),
            }
        )
    result = pd.DataFrame(rows)
    baseline = result[result["scenario"] == "netem_baseline"]
    if not baseline.empty:
        rate = float(baseline.iloc[0]["rows_per_s"])
        result["capture_density_vs_baseline"] = result["rows_per_s"] / rate
    return result


def timesafe_analysis(root: Path) -> pd.DataFrame:
    session_dir = root / "timesafe" / "timesafe_sessions"
    rows: list[dict[str, object]] = []
    for path in sorted(session_dir.glob("*.csv")):
        frame = pd.read_csv(path)
        if frame.empty:
            continue
        rows.append(
            {
                "capture": str(frame.get("capture_id", pd.Series([path.stem])).iloc[0]),
                "segment": path.stem.split("__", 1)[-1],
                "classification": str(frame["label"].iloc[0]),
                "attack_family": str(frame.get("attack_family", pd.Series([""])).iloc[0]),
                "rows": len(frame),
                "start_s": frame["t_s"].min(),
                "end_s": frame["t_s"].max(),
                "duration_s": frame["t_s"].max() - frame["t_s"].min(),
            }
        )
    return pd.DataFrame(rows)


def inventory(root: Path) -> pd.DataFrame:
    rows = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rows.append(
            {
                "relative_path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "extension": path.suffix.lower() or "[none]",
                "sha256": file_sha256(path),
            }
        )
    return pd.DataFrame(rows)


def duplicate_verification(source: Path, project: Path) -> pd.DataFrame:
    """Compare the curated bundle with the project's canonical evidence files."""
    rows: list[dict[str, object]] = []
    for imported in sorted(path for path in source.rglob("*") if path.is_file()):
        relative = imported.relative_to(source)
        parts = relative.parts
        canonical: Path | None = None
        if parts[0] == "timesafe":
            canonical = project / "data" / "external" / Path(*parts[1:])
        elif parts[0] == "Synthetic S-Plane":
            canonical = project / "dataset" / imported.name
        elif parts[0] == "Netem":
            if imported.name in {"splane_telemetry.csv", "splane_windows.csv", "DATASHEET.md"}:
                canonical = project / "dataset" / imported.name
            else:
                canonical = project / "results" / "tier2" / "netem" / Path(*parts[1:])

        canonical_exists = bool(canonical and canonical.is_file())
        identical = bool(
            canonical_exists
            and imported.stat().st_size == canonical.stat().st_size
            and file_sha256(imported) == file_sha256(canonical)
        )
        rows.append(
            {
                "bundle_path": relative.as_posix(),
                "canonical_path": canonical.relative_to(project).as_posix() if canonical else "",
                "canonical_exists": canonical_exists,
                "byte_identical": identical,
            }
        )
    return pd.DataFrame(rows)


def fail_closed_result(root: Path) -> dict[str, object]:
    before = pd.read_csv(root / "Netem" / "fail_closed_live_decisions.csv")
    after = pd.read_csv(root / "Netem" / "fail_closed_live_decisions_after.csv")
    return {
        "before_rows": len(before),
        "before_persisted_protection": float(before["protective_2of3"].mean()),
        "before_labels": ", ".join(f"{k}={v}" for k, v in before["label"].value_counts().items()),
        "after_rows": len(after),
        "after_persisted_protection": float(after["protective_2of3"].mean()),
        "after_labels": ", ".join(f"{k}={v}" for k, v in after["label"].value_counts().items()),
    }


def markdown_report(
    source: Path,
    summary: pd.DataFrame,
    changes: pd.DataFrame,
    netem: pd.DataFrame,
    timesafe: pd.DataFrame,
    files: pd.DataFrame,
    duplicates: pd.DataFrame,
    fail_closed: dict[str, object],
) -> str:
    harmful = summary[summary["classification"].str.startswith("H1")]
    controls = summary[~summary["classification"].str.startswith("H1")]
    real_h1 = int(timesafe.loc[timesafe["classification"] == "H1", "rows"].sum())
    real_h0 = int(timesafe.loc[timesafe["classification"] == "H0", "rows"].sum())
    lines = [
        "# Dataset-Based Problem Localization",
        "",
        "## Decision",
        "",
        "The data supports a three-stage root-cause workflow: first identify the changed signal group, then separate harmful H1 behavior from legitimate H0 changes, and finally inspect the mapped physical or protocol location. The dataset does **not** justify claiming that every anomaly is an attack.",
        "",
        f"Analyzed {len(files):,} curated files ({files['bytes'].sum() / 1024**2:.2f} MiB) from `{source.name}`. The real TIMESAFE derivatives contain {real_h1:,} H1 packet rows and {real_h0:,} H0 packet rows; the simulator contributes {int(summary['event_windows'].sum()):,} labelled event windows plus {int(summary['healthy_control_windows'].sum()):,} scenario-matched healthy controls.",
        "",
        "## Provenance finding",
        "",
        f"{int(duplicates['byte_identical'].sum())} of {len(duplicates)} curated bundle files are byte-for-byte identical to canonical files already present in this project. Therefore, `dataset.zip` is a consolidated copy of existing project evidence, **not a new independent validation dataset**. It remains useful as a submission/archive package, but its duplicate rows must not be mixed into training or counted as additional experiments.",
        "",
        "## Harmful changes and exact first inspection point",
        "",
        "| Change | Evidence signals | Inspect first | Response |",
        "|---|---|---|---|",
    ]
    for row in harmful.itertuples(index=False):
        lines.append(
            f"| {row.change} | `{row.strongest_observed_signals}` | {row.first_location_to_inspect} | {row.operator_response} |"
        )
    lines.extend(
        [
            "",
            "## Legitimate/degraded changes that must not be treated as attacks",
            "",
            "| Change | Classification | Inspect first | Rule |",
            "|---|---|---|---|",
        ]
    )
    for row in controls.itertuples(index=False):
        lines.append(
            f"| {row.change} | {row.classification} | {row.first_location_to_inspect} | {row.operator_response} |"
        )

    lines.extend(
        [
            "",
            "## Real-data cross-checks",
            "",
            "### TIMESAFE",
            "",
            "The bundle contains independent Announce/BMCA, Sync/Follow-Up replay, and Single-Step Sync sessions. Announce captures localize the disturbance to grandmaster election; the Sync families localize it to PTP sequence/timing delivery. Capture identity must remain the holdout boundary during model evaluation because rows inside a session are highly correlated.",
            "",
            "### Linux/netem transport experiments",
            "",
            "| Scenario | Rows | Density vs baseline | |offset| p95 ns | PDV std ns | Meaning |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    meanings = {
        "netem_baseline": "Reference transport behavior",
        "netem_pdv": "Delay variation/congestion at the fronthaul transport",
        "netem_loss": "Packet loss/sparse timing delivery on the fronthaul link",
        "netem_holdover": "Timing-source loss/holdover; only a small observable sample exists",
    }
    for row in netem.itertuples(index=False):
        lines.append(
            f"| {row.scenario} | {row.rows:,} | {row.capture_density_vs_baseline:.3f} | {fmt(row.offset_abs_p95_ns)} | {fmt(row.pdv_std_ns)} | {meanings.get(row.scenario, '')} |"
        )

    lines.extend(
        [
            "",
            "### Missing/stale telemetry safety defect",
            "",
            f"Before the fail-closed change, all {fail_closed['before_rows']} outage windows were labelled `{fail_closed['before_labels']}` and persisted protection was {100 * fail_closed['before_persisted_protection']:.2f}%. After the change, labels became `{fail_closed['after_labels']}` and persisted protection was {100 * fail_closed['after_persisted_protection']:.2f}%. This localizes the original failure to the **telemetry validity/decision gate**, not to the classifier.",
            "",
            "## Operational localization rules",
            "",
            "1. BMCA fields change with a large offset step: inspect Announce origin and grandmaster election.",
            "2. Sequence regressions or message irregularity without a GM change: inspect Sync/Follow-Up delivery for replay or reordering.",
            "3. Message rate rises alone: compare with the legitimate traffic-burst control before declaring DoS.",
            "4. PDV/path delay rises while PTP identities remain stable: inspect switches, queues, QoS, and link loss.",
            "5. Satellite count/status and holdover change: inspect GNSS antenna/receiver and oscillator behavior.",
            "6. SyncE QL degrades: inspect the Ethernet Equipment Clock chain, not the GNSS receiver.",
            "7. Telemetry is absent, stale, NaN, or provenance-less: bypass ML and route to UNKNOWN/safe-default.",
            "",
            "## What is final and what is not",
            "",
            "The dataset is sufficient to finalize the software localization matrix above and to validate replay, Announce takeover, transport impairment, GNSS loss/jam, and telemetry-loss paths. It is not sufficient to certify physical O-DU/O-RU hardware behavior or reliably detect a healthy-looking unseen GNSS spoof. That last case requires authenticated GNSS or an independent physical clock (Tier 3).",
            "",
            "## Reproducible outputs",
            "",
            "- `scenario_localization.csv`: change-to-location decision matrix.",
            "- `feature_changes.csv`: measured healthy-to-event feature deltas.",
            "- `netem_summary.csv`: real transport-impairment summary.",
            "- `timesafe_session_summary.csv`: real capture/segment boundaries and row counts.",
            "- `dataset_inventory.csv`: file sizes and SHA-256 provenance hashes.",
            "- `duplicate_verification.csv`: byte-level comparison with canonical project evidence.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    project = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-root",
        type=Path,
        default=project / "data" / "external" / "dataset_2026-08-30",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=project / "results" / "dataset_2026-08-30",
    )
    args = parser.parse_args()
    source = args.data_root.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)

    summary, changes = simulation_analysis(source)
    netem = netem_analysis(source)
    timesafe = timesafe_analysis(source)
    files = inventory(source)
    duplicates = duplicate_verification(source, project)
    fail_closed = fail_closed_result(source)

    summary.to_csv(output / "scenario_localization.csv", index=False)
    changes.to_csv(output / "feature_changes.csv", index=False)
    netem.to_csv(output / "netem_summary.csv", index=False)
    timesafe.to_csv(output / "timesafe_session_summary.csv", index=False)
    files.to_csv(output / "dataset_inventory.csv", index=False)
    duplicates.to_csv(output / "duplicate_verification.csv", index=False)
    report = markdown_report(
        source, summary, changes, netem, timesafe, files, duplicates, fail_closed
    )
    (output / "PROBLEM_LOCALIZATION_REPORT.md").write_text(report, encoding="utf-8")

    print(f"Wrote problem-localization analysis to {output}")
    print(f"Scenarios localized: {len(summary)}")
    print(f"Curated files inventoried: {len(files)}")


if __name__ == "__main__":
    main()
