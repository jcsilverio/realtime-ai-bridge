"""Fail-closed behavior of the selection graph, driven by a scripted fake model."""

from pathlib import Path

import pytest

from fakes import FakeModel
from orchestrator.graph import ClipPick, build_graph, initial_state
from orchestrator.schemas import MotionExport


@pytest.fixture
def written() -> list:
    return []


def run(model: FakeModel, written: list) -> dict:
    def record(export: MotionExport) -> Path:
        written.append(export)
        return Path("fake.json")

    return build_graph(llm=model, writer=record).invoke(initial_state("scripted intent"))


def test_passing_pick_writes_one_export(written: list) -> None:
    result = run(FakeModel(["emote"], ["Crying_Montage"], [True]), written)
    assert result["failure"] is None
    assert [export.clip_id for export in written] == ["Crying_Montage"]
    assert written[0].source == "agent"


def test_null_pick_writes_nothing(written: list) -> None:
    result = run(FakeModel(["interact"], [None], []), written)
    assert result["failure"] == "no_fit"
    assert written == []


def test_unknown_clip_id_writes_nothing(written: list) -> None:
    result = run(FakeModel(["emote"], ["Wave_Montage"], []), written)
    assert result["failure"] == "invalid_pick"
    assert written == []


def test_clip_outside_chosen_categories_writes_nothing(written: list) -> None:
    result = run(FakeModel(["emote"], ["Punch_Jab_Montage"], []), written)
    assert result["failure"] == "invalid_pick"
    assert written == []


def test_rejection_after_retry_writes_nothing(written: list) -> None:
    model = FakeModel(["emote"], ["Celebration_Montage", "Dance_Loop_Montage"], [False, False])
    result = run(model, written)
    assert result["failure"] == "rejected"
    assert result["rejected_clip_ids"] == ["Celebration_Montage", "Dance_Loop_Montage"]
    assert written == []


def test_retry_excludes_rejected_clip(written: list) -> None:
    model = FakeModel(["emote"], ["Celebration_Montage", "Crying_Montage"], [False, True])
    run(model, written)
    _, (_, retry_message) = model.pickers[ClipPick].calls[1]
    assert "Celebration_Montage" not in retry_message
    assert [export.clip_id for export in written] == ["Crying_Montage"]
