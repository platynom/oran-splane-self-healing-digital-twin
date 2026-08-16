from __future__ import annotations

"""Run the deterministic Phase-1 replay robustness pilot."""

import itertools
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evasion.harness import ReplayParameters, RobustnessHarness


def pilot_candidates() -> list[ReplayParameters]:
    candidates: list[ReplayParameters] = []
    for index, (magnitude, cadence, ramp, fields) in enumerate(
        itertools.product(
            (40.0, 90.0, 140.0),
            (0.04, 0.10, 0.20),
            (0.0, 30.0),
            (("sequence_id",), ("sequence_id", "origin_timestamp")),
        )
    ):
        candidates.append(
            ReplayParameters(
                magnitude_ns=magnitude,
                injection_cadence_s=cadence,
                ramp_rate_ns_per_s=ramp,
                forged_fields=fields,
                replay_depth=1 + index % 3,
                seed=1588 + index,
            )
        )
    return candidates


def main() -> None:
    harness = RobustnessHarness(ROOT)
    results = harness.sweep(pilot_candidates())
    output = ROOT / "results" / "evasion" / "harness_replay_pilot.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output, index=False)
    impactful = results[results["exceeds_budget"]]
    print(f"wrote {output}")
    print(f"candidates: {len(results)}")
    print(f"exceeded budget: {len(impactful)}")
    for column in ("transformer_flagged", "rf_flagged", "openset_flagged"):
        overall = float(results[column].mean())
        impactful_rate = float(impactful[column].mean()) if len(impactful) else float("nan")
        print(f"{column}: overall={overall:.2%}, impactful={impactful_rate:.2%}")
    if impactful.empty:
        raise SystemExit("pilot failed: no replay candidate exceeded the timing budget")


if __name__ == "__main__":
    main()
