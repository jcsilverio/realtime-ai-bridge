"""Integration contract between the orchestrator and the Unreal montage consumer."""

from __future__ import annotations

from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

MotionSource = Literal["stub"]


class MotionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: str


class MotionExport(BaseModel):
    """Motion export for Unreal. clip_id names the montage to play."""

    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(default_factory=lambda: str(uuid4()))
    source: MotionSource
    clip_id: str
    metadata: dict[str, str] = Field(default_factory=dict)
