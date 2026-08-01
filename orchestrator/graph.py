"""Minimal LangGraph: intent, stub, export write."""

from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from inference.stub import generate_motion_stub
from orchestrator.export_writer import write_export
from orchestrator.schemas import MotionExport, MotionRequest


class MotionGraphState(TypedDict):
    intent: str
    export: MotionExport | None
    export_path: str | None
    error: str | None


def generate_node(state: MotionGraphState) -> dict:
    request = MotionRequest(intent=state["intent"])
    export = generate_motion_stub(request)
    if export is None:
        return {
            "export": None,
            "error": f"No clip match for intent: {state['intent']!r}",
        }
    return {"export": export, "error": None}


def write_node(state: MotionGraphState) -> dict:
    path = write_export(state["export"])
    return {"export_path": str(path)}


def route_after_generate(state: MotionGraphState) -> Literal["write", "__end__"]:
    if state.get("export") is None:
        return "__end__"
    return "write"


def build_graph():
    graph = StateGraph(MotionGraphState)
    graph.add_node("generate", generate_node)
    graph.add_node("write", write_node)
    graph.add_edge(START, "generate")
    graph.add_conditional_edges(
        "generate",
        route_after_generate,
        {"write": "write", "__end__": END},
    )
    graph.add_edge("write", END)
    return graph.compile()