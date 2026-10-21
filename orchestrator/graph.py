"""LangGraph orchestrator that selects categories, picks a clip, and writes the export."""

from __future__ import annotations

from functools import partial
from typing import Literal, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict, Field

from orchestrator.catalog import Category, by_category
from orchestrator.config import MODEL_NAME, REASONING_EFFORT
from orchestrator.export_writer import write_export
from orchestrator.prompts import CATEGORY_SYSTEM_PROMPT, MOTION_SYSTEM_PROMPT, format_candidates
from orchestrator.schemas import MotionExport


class CategoryPick(BaseModel):
    model_config = ConfigDict(extra="forbid")

    categories: list[Category] = Field(min_length=1, max_length=2)


class ClipPick(BaseModel):
    model_config = ConfigDict(extra="forbid")

    clip_id: str | None


class MotionGraphState(TypedDict):
    intent: str
    categories: list[Category]
    clip_id: str | None
    export: MotionExport | None
    export_path: str | None
    error: str | None


def select_categories_node(state: MotionGraphState, picker: Runnable) -> dict:
    pick = picker.invoke([("system", CATEGORY_SYSTEM_PROMPT), ("human", state["intent"])])
    return {"categories": pick.categories}


def select_motion_node(state: MotionGraphState, picker: Runnable) -> dict:
    candidates = [clip for category in state["categories"] for clip in by_category(category)]
    pick = picker.invoke(
        [
            ("system", MOTION_SYSTEM_PROMPT),
            ("human", format_candidates(state["intent"], candidates)),
        ]
    )
    if pick.clip_id is None:
        return {"clip_id": None, "error": f"No clip fits intent: {state['intent']!r}"}
    if pick.clip_id not in {clip.clip_id for clip in candidates}:
        return {"clip_id": None, "error": f"Model picked {pick.clip_id!r}, which is not a candidate"}
    return {"clip_id": pick.clip_id}


def write_node(state: MotionGraphState) -> dict:
    export = MotionExport(
        source="agent",
        clip_id=state["clip_id"],
        metadata={"intent": state["intent"], "categories": ",".join(state["categories"])},
    )
    path = write_export(export)
    return {"export": export, "export_path": str(path)}


def route_after_select(state: MotionGraphState) -> Literal["write", "__end__"]:
    if state.get("clip_id") is None:
        return "__end__"
    return "write"


def build_graph(llm: BaseChatModel | None = None):
    if llm is None:
        llm = ChatOpenAI(model=MODEL_NAME, reasoning_effort=REASONING_EFFORT)
    category_picker = llm.with_structured_output(CategoryPick)
    motion_picker = llm.with_structured_output(ClipPick)

    graph = StateGraph(MotionGraphState)
    graph.add_node("select_categories", partial(select_categories_node, picker=category_picker))
    graph.add_node("select_motion", partial(select_motion_node, picker=motion_picker))
    graph.add_node("write", write_node)
    graph.add_edge(START, "select_categories")
    graph.add_edge("select_categories", "select_motion")
    graph.add_conditional_edges(
        "select_motion",
        route_after_select,
        {"write": "write", "__end__": END},
    )
    graph.add_edge("write", END)
    return graph.compile()
