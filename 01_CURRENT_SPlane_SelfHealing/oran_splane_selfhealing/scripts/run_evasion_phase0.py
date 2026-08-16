from __future__ import annotations

"""Run the Step-1 victim reproduction and write its evidence artifacts."""

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evasion.victim_transformer import (
    GATE_THRESHOLD,
    evaluate_project_victim,
    evaluate_transformer_victim,
    load_capture_sessions,
    save_transformer_checkpoint,
    session_holdout,
    train_transformer_victim,
)


def run(epochs: int = 6, batch_size: int = 512) -> pd.DataFrame:
    sessions = load_capture_sessions(ROOT)
    train_ids, test_ids, split_index = session_holdout(sessions)
    print(f"session split candidate: {split_index}")
    print(f"train sessions: {', '.join(train_ids)}")
    print(f"test sessions: {', '.join(test_ids)}")
    transformer = train_transformer_victim(
        sessions,
        train_ids,
        test_ids,
        epochs=epochs,
        batch_size=batch_size,
    )
    transformer_row, per_capture = evaluate_transformer_victim(transformer, sessions)
    project_row = evaluate_project_victim(ROOT, train_ids, test_ids)
    results = pd.DataFrame([transformer_row, project_row])

    out_dir = ROOT / "results" / "evasion"
    out_dir.mkdir(parents=True, exist_ok=True)
    results.to_csv(out_dir / "victim_repro.csv", index=False)
    per_capture.to_csv(out_dir / "victim_transformer_by_capture.csv", index=False)
    save_transformer_checkpoint(transformer, out_dir / "victim_transformer.pt")

    transformer_accuracy = float(transformer_row["accuracy"])
    project_accuracy = float(project_row["accuracy"])
    gate_passed = transformer_accuracy >= GATE_THRESHOLD
    notes = f"""# Evasion Phase 0 — Victim Reproduction

## Scope and data provenance

These are **real public capture** results from the TIMESAFE repository; they are not simulator or
live-network numbers. Packet features were decoded directly from the five public pcaps and aligned
row-for-row with the released labels. The operational RF victim used the corresponding canonical
telemetry CSVs in `data/external/timesafe_sessions/`.

Complete `capture_id` groups were assigned with `GroupShuffleSplit`; no overlapping packet or
telemetry window crosses train/test. Split candidate {split_index} retained Announce and Sync attack
families on both sides without inspecting test performance.

- Train sessions: `{', '.join(train_ids)}`
- Test sessions: `{', '.join(test_ids)}`
- Transformer: 40-packet window, stride 2, five per-packet features (direction, length, sequence ID,
  message type, inter-arrival), two encoder layers, CPU-only, {epochs} fixed epochs.
- Project victim: existing `discriminator.model.train_and_evaluate` API plus existing open-set detector
  and 2-of-3 persistence; protected modules were imported, not modified.

## Results

| Victim | Accuracy | Confusion matrix `[[TN,FP],[FN,TP]]` |
|---|---:|---|
| TIMESAFE-class Transformer | {transformer_accuracy:.6f} | `{transformer_row['confusion_matrix']}` |
| Project RF + open-set + 2-of-3 | {project_accuracy:.6f} | `{project_row['confusion_matrix']}` |

Per-capture Transformer results are in `results/evasion/victim_transformer_by_capture.csv`.

## Phase-0 gate

**{'PASS' if gate_passed else 'FAIL'}** — the pre-registered reproduction threshold is
{GATE_THRESHOLD:.0%}; observed held-session accuracy is {transformer_accuracy:.2%}.
{'Step 2 may be considered only after independent reviewer approval of this handoff.' if gate_passed else 'Do not proceed to Step 2. The TIMESAFE-class victim did not clear the gate; a human decision is required.'}

## Deviations and caveats

- The released reference implementation randomly reuses chunks for validation and testing. This
  reproduction instead uses the required complete-session holdout, so its number is intentionally
  leakage-resistant rather than a byte-for-byte recreation of that split.
- Announce sessions 1 and 2 are distinct released pcap paths with identical packet streams but
  different released attack intervals. They remain separate declared capture IDs, and neither appears
  in the test set.
- The existing project victim API cannot stratify a label/scenario stratum containing one window.
  Its adapter excludes the two one-window benign fragments from Announce sessions 1 and 2 during
  training only; no held-session row is removed.
- PyTorch is required only for this CPU-gated research victim. The existing project pipeline remains
  CPU-runnable without enabling the Transformer victim.
"""
    (ROOT / "docs" / "EVASION_PHASE0_NOTES.md").write_text(notes, encoding="utf-8")
    print(results.to_string(index=False))
    print(f"training loss: {[round(value, 6) for value in transformer.training_loss]}")
    print(f"gate: {'PASS' if gate_passed else 'FAIL'}")
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument("--batch-size", type=int, default=512)
    args = parser.parse_args()
    run(epochs=args.epochs, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
