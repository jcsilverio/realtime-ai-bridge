"""Integration contract between ML or orchestrator output and the Unreal consumer."""

from __future__ import annotations

from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


Emotion = Literal["neutral", "happy", "angry", "sad"]
MotionSource = Literal["inference", "stub", "fallback_clip"]


class MotionRequest(BaseModel):
    intent: str
    emotion: Emotion | None = None
    duration_sec: float = 2.0
    target_fps: int = 30
    rig_id: str = "proxy_ue_mannequin"


class MotionFrame(BaseModel):
    time_sec: float
    root_translation: tuple[float, float, float] = (0.0, 0.0, 0.0)
    joint_rotations: dict[str, tuple[float, float, float]] = Field(default_factory=dict)


class MotionExport(BaseModel):
    """Motion export for Unreal. clip_id selects preset animations. frames is optional."""

    request_id: str = Field(default_factory=lambda: str(uuid4()))
    source: MotionSource
    clip_id: str | None = None
    play_rate: float = 1.0
    blend_in_sec: float = 0.2
    fps: int | None = None
    frames: list[MotionFrame] | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
