#!/usr/bin/env python3
"""Write stub motion export to exports/latest.json."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from inference.stub import generate_motion_stub
from orchestrator.export_writer import write_export
from orchestrator.schemas import MotionRequest


def main() -> None:
    intent = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "make the character wave hello"
    request = MotionRequest(intent=intent)
    export = generate_motion_stub(request)
    if export is None:
        print(f"No clip match for intent: {intent!r}")
        raise SystemExit(1)
    path = write_export(export)
    print(f"Wrote {path}")
    print(f"  source={export.source} clip_id={export.clip_id}")


if __name__ == "__main__":
    main()
