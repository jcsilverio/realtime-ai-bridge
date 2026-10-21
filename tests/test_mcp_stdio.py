"""Launches the MCP server as a subprocess and talks to it over stdio, the way a client does."""

import asyncio
import json
import sys
from pathlib import Path

from mcp.client import Client
from mcp.client.stdio import StdioServerParameters

from orchestrator.catalog import get_catalog
from orchestrator.paths import REPO_ROOT

SERVER = REPO_ROOT / "mcp_server" / "server.py"


async def talk_to_server(cwd: Path) -> tuple[set[str], dict, list[str]]:
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)], cwd=cwd)
    async with Client(params, read_timeout_seconds=30) as client:
        tools = await client.list_tools()
        catalog = await client.read_resource("motion://catalog")
        react = await client.call_tool("list_motions", {"category": "react"})
    return (
        {tool.name for tool in tools.tools},
        json.loads(catalog.contents[0].text),
        [clip["clip_id"] for clip in react.structured_content["result"]],
    )


def test_server_answers_over_stdio(tmp_path: Path) -> None:
    # Clients start the server from their own folder, so this runs it from outside the repo.
    # play_motion is left out because the server loads .env and would call the real model.
    tool_names, catalog, react_ids = asyncio.run(talk_to_server(tmp_path))
    assert tool_names == {"list_motions", "play_motion"}
    assert len(catalog["clips"]) == len(get_catalog().clips)
    assert react_ids == ["Hit_Head_Montage", "Hit_Stomach_Montage"]
