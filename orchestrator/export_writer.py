"""Atomic write of MotionExport JSON for Unreal polling."""

from __future__ import annotations

import json
from pathlib import Path

from orchestrator.paths import EXPORTS_DIR, LATEST_EXPORT
from orchestrator.schemas import MotionExport


def write_export(export: MotionExport, path: Path | None = None) -> Path:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    target = path or LATEST_EXPORT
    tmp = target.with_suffix(".json.tmp")
    payload = export.model_dump(mode="json")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(target)
    return target
