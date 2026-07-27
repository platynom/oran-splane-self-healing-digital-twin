from __future__ import annotations

import argparse

from oran_twin.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AI-native O-RAN Digital Twin MVP demo.")
    parser.add_argument("--run-name", default="demo")
    parser.add_argument("--duration", type=int, default=240)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    out_dir = run_pipeline(run_name=args.run_name, duration=args.duration, seed=args.seed)
    print(f"Demo outputs written to: {out_dir}")
    print(f"Open dashboard: {out_dir / 'dashboard.html'}")


if __name__ == "__main__":
    main()
