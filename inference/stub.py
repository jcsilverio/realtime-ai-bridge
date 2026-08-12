"""Keyword stub for motion clip selection."""

from __future__ import annotations

import time

from orchestrator.schemas import MotionExport, MotionRequest


def generate_motion_stub(request: MotionRequest) -> MotionExport | None:
    started = time.perf_counter()
    text = request.intent.lower()

    if any(k in text for k in ("wave", "hello", "greet")):
        clip_id = "AM_Wave_01"
    elif any(k in text for k in ("point", "look", "there")):
        clip_id = "AM_Point_01"
    elif any(k in text for k in ("dance", "celebrate", "groove", "boogie")):
        clip_id = "AM_Dance_01"
    else:
        return None


    latency_ms = str(int((time.perf_counter() - started) * 1000))

    return MotionExport(
        source="stub",
        clip_id=clip_id,
        play_rate=1.0,
        blend_in_sec=0.2,
        metadata={
            "latency_ms": latency_ms,
            "device": "stub",
            "intent": request.intent,
        },
    )
