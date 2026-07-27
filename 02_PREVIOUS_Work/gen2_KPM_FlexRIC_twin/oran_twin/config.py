from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Paths:
    root: Path = ROOT
    configs: Path = ROOT / "configs"
    outputs: Path = ROOT / "outputs"
    runs: Path = ROOT / "outputs" / "runs"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)

