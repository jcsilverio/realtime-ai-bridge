"""MCP server tools, driven by the scripted fake model so no API key is needed."""

import asyncio
from pathlib import Path
from typing import get_args

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from fakes import FakeModel
from mcp_server.server import list_motions, play_intent, play_motion, server
from orchestrator.catalog import Category, get_catalog
from orchestrator.graph import build_graph
from orchestrator.schemas import MotionExport


def play(model: FakeModel, written: list):
    def record(export: MotionExport) -> Path:
        written.append(export)
        return Path("fake.json")

    return play_intent("scripted intent", build_graph(llm=model, writer=record))


def test_played_clip_matches_the_written_export() -> None:
    written: list = []
    result = play(FakeModel(["emote"], ["Crying_Montage"], [True]), written)
    assert result.played
    assert result.clip_id == "Crying_Montage"
    assert result.request_id == written[0].request_id


def test_no_fit_reports_why_and_writes_nothing() -> None:
    written: list = []
    result = play(FakeModel(["interact"], [None], []), written)
    assert not result.played
    assert result.failure == "no_fit"
    assert result.reason
    assert written == []


def test_rejection_reports_failure_and_writes_nothing() -> None:
    written: list = []
    model = FakeModel(["emote"], ["Celebration_Montage", "Dance_Loop_Montage"], [False, False])
    result = play(model, written)
    assert result.failure == "rejected"
    assert written == []


def test_play_motion_without_key_raises_tool_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ToolError, match="OPENAI_API_KEY"):
        play_motion("throw a quick jab")


def test_list_motions_filters_by_category() -> None:
    assert len(list_motions()) == len(get_catalog().clips)
    cast = list_motions("cast")
    assert cast
    assert {clip.category for clip in cast} == {"cast"}


def test_tool_schemas_an_agent_sees() -> None:
    """The input schemas are what an MCP client shows the model."""
    tools = {tool.name: tool for tool in asyncio.run(server.list_tools())}
    assert set(tools) == {"list_motions", "play_motion"}
    assert set(tools["play_motion"].input_schema["properties"]) == {"intent"}
    category = tools["list_motions"].input_schema["properties"]["category"]
    # Category | None becomes anyOf with the enum first and null second.
    assert category["anyOf"][0]["enum"] == list(get_args(Category))
