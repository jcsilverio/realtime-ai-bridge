#!/usr/bin/env python3
"""MCP server that lets an agent read the motion catalog and play a clip in Unreal."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel

from orchestrator.catalog import CatalogClip, Category, by_category, get_catalog
from orchestrator.graph import Failure, build_graph, initial_state
from orchestrator.schemas import MotionExport

server = MCPServer(
    "realtime-ai-bridge",
    instructions=(
        "Plays character animations in a running Unreal Engine scene. "
        "Read motion://catalog to see what the character can do, then call play_motion."
    ),
)


class PlayResult(BaseModel):
    played: bool
    clip_id: str | None = None
    request_id: str | None = None
    failure: Failure | None = None
    reason: str | None = None


@server.resource("motion://catalog", mime_type="application/json")
def catalog() -> str:
    """Every clip the character can play, with its category and description."""
    return get_catalog().model_dump_json(indent=2)


@server.resource("motion://contract", mime_type="application/json")
def contract() -> str:
    """JSON schema of the export file that Unreal reads."""
    return json.dumps(MotionExport.model_json_schema(), indent=2)


@server.tool()
def list_motions(category: Category | None = None) -> list[CatalogClip]:
    """List the clips the character can play, optionally for one category."""
    if category is None:
        return list(get_catalog().clips)
    return list(by_category(category))


# Kept outside the tool because a tool's parameters are the schema the agent sees,
# so tests pass a graph built on the fake model here instead.
def play_intent(intent: str, graph) -> PlayResult:
    result = graph.invoke(initial_state(intent))
    if result["failure"]:
        return PlayResult(played=False, failure=result["failure"], reason=result["error"])
    export = result["export"]
    return PlayResult(
        played=True,
        clip_id=export.clip_id,
        request_id=export.request_id,
        reason=result["eval_reason"],
    )


@server.tool()
def play_motion(intent: str) -> PlayResult:
    """Play the clip that best fits a plain-language request, such as "throw a quick jab".

    played means the export was written for Unreal to pick up. Unreal does not confirm
    playback, so nothing appears unless the scene is running. Nothing plays if no clip
    fits or the pick fails review. Then played is false and reason says why. Do not
    retry with the same request.
    """
    if not os.environ.get("OPENAI_API_KEY"):
        # Only a ToolError's message reaches the agent. Any other exception shows up
        # as a generic crash.
        raise ToolError("OPENAI_API_KEY is not set. Copy .env.example to .env and add your key.")
    return play_intent(intent, build_graph())


if __name__ == "__main__":
    load_dotenv(ROOT / ".env")
    server.run()
