"""Keyword stub for motion clip selection."""

from __future__ import annotations

import time

from orchestrator.schemas import MotionExport, MotionRequest


def generate_motion_stub(request: MotionRequest) -> MotionExport | None:
    started = time.perf_counter()
    text = request.intent.lower()

    if any(k in text for k in ("jab", "punch")):
        clip_id = "Punch_Jab_Montage"
    elif any(k in text for k in ("celebrate", "victory", "cheer")):
        clip_id = "Celebration_Montage"
    elif any(k in text for k in ("dance", "groove", "boogie")):
        clip_id = "Dance_Loop_Montage"
    else:
        return None

    latency_ms = str(int((time.perf_counter() - started) * 1000))

    return MotionExport(
        source="stub",
        clip_id=clip_id,
        metadata={
            "latency_ms": latency_ms,
            "intent": request.intent,
        },
    )
