"""LangGraph orchestrator that selects categories, picks a clip, and writes the export."""

from __future__ import annotations

from functools import partial
from typing import Literal, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict, Field

from inference.stub import generate_motion_stub
from orchestrator.catalog import Category
from orchestrator.config import MODEL_NAME, REASONING_EFFORT
from orchestrator.export_writer import write_export
from orchestrator.prompts import CATEGORY_SYSTEM_PROMPT
from orchestrator.schemas import MotionExport, MotionRequest


class CategoryPick(BaseModel):
    model_config = ConfigDict(extra="forbid")

    categories: list[Category] = Field(min_length=1, max_length=2)


class MotionGraphState(TypedDict):
    intent: str
    categories: list[Category]
    export: MotionExport | None
    export_path: str | None
    error: str | None


def select_categories_node(state: MotionGraphState, picker: Runnable) -> dict:
    pick = picker.invoke([("system", CATEGORY_SYSTEM_PROMPT), ("human", state["intent"])])
    return {"categories": pick.categories}


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


def build_graph(llm: BaseChatModel | None = None):
    if llm is None:
        llm = ChatOpenAI(model=MODEL_NAME, reasoning_effort=REASONING_EFFORT)
    category_picker = llm.with_structured_output(CategoryPick)

    graph = StateGraph(MotionGraphState)
    graph.add_node("select_categories", partial(select_categories_node, picker=category_picker))
    graph.add_node("generate", generate_node)
    graph.add_node("write", write_node)
    graph.add_edge(START, "select_categories")
    graph.add_edge("select_categories", "generate")
    graph.add_conditional_edges(
        "generate",
        route_after_generate,
        {"write": "write", "__end__": END},
    )
    graph.add_edge("write", END)
    return graph.compile()
