"""LangGraph orchestrator that picks categories, then a clip, checks it, and writes the export."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Literal, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict, Field

from orchestrator.catalog import Category, by_category, get
from orchestrator.config import MAX_RETRIES, MODEL_NAME, REASONING_EFFORT
from orchestrator.export_writer import write_export
from orchestrator.prompts import (
    CATEGORY_SYSTEM_PROMPT,
    EVALUATOR_SYSTEM_PROMPT,
    MOTION_SYSTEM_PROMPT,
    format_candidates,
    format_evaluation,
)
from orchestrator.schemas import MotionExport

Failure = Literal["no_fit", "invalid_pick", "rejected"]
ExportWriter = Callable[[MotionExport], Path]


class CategoryPick(BaseModel):
    model_config = ConfigDict(extra="forbid")

    categories: list[Category] = Field(min_length=1, max_length=2)


class ClipPick(BaseModel):
    model_config = ConfigDict(extra="forbid")

    clip_id: str | None


class EvalVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Field order is the order the model writes, so the reason comes before the verdict.
    reason: str
    passed: bool


class MotionGraphState(TypedDict):
    intent: str
    categories: list[Category]
    clip_id: str | None
    rejected_clip_ids: list[str]
    eval_passed: bool | None
    eval_reason: str | None
    failure: Failure | None
    error: str | None
    export: MotionExport | None
    export_path: str | None


def initial_state(intent: str) -> MotionGraphState:
    return {
        "intent": intent,
        "categories": [],
        "clip_id": None,
        "rejected_clip_ids": [],
        "eval_passed": None,
        "eval_reason": None,
        "failure": None,
        "error": None,
        "export": None,
        "export_path": None,
    }


def failed(failure: Failure, error: str) -> dict:
    return {"clip_id": None, "failure": failure, "error": error}


def select_categories_node(state: MotionGraphState, picker: Runnable) -> dict:
    pick = picker.invoke([("system", CATEGORY_SYSTEM_PROMPT), ("human", state["intent"])])
    return {"categories": pick.categories}


def select_motion_node(state: MotionGraphState, picker: Runnable) -> dict:
    candidates = [
        clip
        for category in state["categories"]
        for clip in by_category(category)
        # A retry without the rejected clip in view is the only way to get a different pick.
        if clip.clip_id not in state["rejected_clip_ids"]
    ]
    if not candidates:
        return failed("no_fit", f"No candidate clips left for intent: {state['intent']!r}")
    pick = picker.invoke(
        [
            ("system", MOTION_SYSTEM_PROMPT),
            ("human", format_candidates(state["intent"], candidates)),
        ]
    )
    if pick.clip_id is None:
        return failed("no_fit", f"No clip fits intent: {state['intent']!r}")
    if pick.clip_id not in {clip.clip_id for clip in candidates}:
        return failed("invalid_pick", f"Model picked {pick.clip_id!r}, which is not a candidate")
    return {"clip_id": pick.clip_id}


def evaluate_node(state: MotionGraphState, judge: Runnable) -> dict:
    # route_after_select only reaches this node with a validated candidate id.
    clip = get(state["clip_id"])
    verdict = judge.invoke(
        [
            ("system", EVALUATOR_SYSTEM_PROMPT),
            ("human", format_evaluation(state["intent"], clip)),
        ]
    )
    if verdict.passed:
        return {"eval_passed": True, "eval_reason": verdict.reason}
    rejected = [*state["rejected_clip_ids"], clip.clip_id]
    update = {
        "clip_id": None,
        "eval_passed": False,
        "eval_reason": verdict.reason,
        "rejected_clip_ids": rejected,
    }
    if len(rejected) > MAX_RETRIES:
        update["failure"] = "rejected"
        update["error"] = f"Evaluator rejected {clip.clip_id}: {verdict.reason}"
    return update


def write_node(state: MotionGraphState, writer: ExportWriter) -> dict:
    export = MotionExport(
        source="agent",
        clip_id=state["clip_id"],
        metadata={"intent": state["intent"], "categories": ",".join(state["categories"])},
    )
    path = writer(export)
    return {"export": export, "export_path": str(path)}


def route_after_select(state: MotionGraphState) -> Literal["evaluate", "__end__"]:
    if state["clip_id"] is None:
        return "__end__"
    return "evaluate"


def route_after_evaluate(state: MotionGraphState) -> Literal["write", "select_motion", "__end__"]:
    if state["eval_passed"]:
        return "write"
    if state["failure"] is None:
        return "select_motion"
    return "__end__"


def build_graph(llm: BaseChatModel | None = None, writer: ExportWriter | None = None):
    """Defaults to the configured OpenAI model and the real export file.

    Tests and the eval pass their own.
    """
    if llm is None:
        llm = ChatOpenAI(model=MODEL_NAME, reasoning_effort=REASONING_EFFORT)
    if writer is None:
        writer = write_export
    category_picker = llm.with_structured_output(CategoryPick)
    motion_picker = llm.with_structured_output(ClipPick)
    judge = llm.with_structured_output(EvalVerdict)

    graph = StateGraph(MotionGraphState)
    graph.add_node("select_categories", partial(select_categories_node, picker=category_picker))
    graph.add_node("select_motion", partial(select_motion_node, picker=motion_picker))
    graph.add_node("evaluate", partial(evaluate_node, judge=judge))
    graph.add_node("write", partial(write_node, writer=writer))
    graph.add_edge(START, "select_categories")
    graph.add_edge("select_categories", "select_motion")
    graph.add_conditional_edges(
        "select_motion",
        route_after_select,
        {"evaluate": "evaluate", "__end__": END},
    )
    graph.add_conditional_edges(
        "evaluate",
        route_after_evaluate,
        {"write": "write", "select_motion": "select_motion", "__end__": END},
    )
    graph.add_edge("write", END)
    return graph.compile()
