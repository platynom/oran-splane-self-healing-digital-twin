from __future__ import annotations

import json
from pathlib import Path

from .config import Paths


class ModelRegistry:
    """Local model registry metadata for versioning and rollback planning."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Paths.configs / "model_registry.json"

    def snapshot(self) -> dict[str, object]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def active_models(self) -> dict[str, str]:
        data = self.snapshot()
        return dict(data.get("active_models", {}))
