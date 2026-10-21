"""Fail-closed behavior of the selection graph, driven by a scripted fake model."""

import pytest

from orchestrator import graph
from orchestrator.graph import CategoryPick, ClipPick, EvalVerdict, build_graph, initial_state


class ScriptedPicker:
    def __init__(self, replies: list) -> None:
        self.replies = list(replies)
        self.calls: list = []

    def invoke(self, messages: list) -> object:
        self.calls.append(messages)
        # An unscripted extra call raises IndexError, which is how tests catch a missed retry limit.
        return self.replies.pop(0)


class FakeModel:
    """Returns scripted replies per output schema.

    LangChain's fake chat models do not implement with_structured_output.
    """

    def __init__(
        self, categories: list[str], clips: list[str | None], verdicts: list[bool]
    ) -> None:
        self.pickers = {
            CategoryPick: ScriptedPicker([CategoryPick(categories=categories)]),
            ClipPick: ScriptedPicker([ClipPick(clip_id=clip_id) for clip_id in clips]),
            EvalVerdict: ScriptedPicker(
                [EvalVerdict(reason="scripted", passed=p) for p in verdicts]
            ),
        }

    def with_structured_output(self, schema: type) -> ScriptedPicker:
        return self.pickers[schema]


@pytest.fixture
def written(monkeypatch: pytest.MonkeyPatch) -> list:
    exports = []

    def fake_write(export):
        exports.append(export)
        return "fake.json"

    # Patch the name graph.py imported, so the real exports/latest.json is never touched.
    monkeypatch.setattr(graph, "write_export", fake_write)
    return exports


def run(model: FakeModel) -> dict:
    return build_graph(llm=model).invoke(initial_state("scripted intent"))


def test_passing_pick_writes_one_export(written: list) -> None:
    result = run(FakeModel(["emote"], ["Crying_Montage"], [True]))
    assert result["failure"] is None
    assert [export.clip_id for export in written] == ["Crying_Montage"]
    assert written[0].source == "agent"


def test_null_pick_writes_nothing(written: list) -> None:
    result = run(FakeModel(["interact"], [None], []))
    assert result["failure"] == "no_fit"
    assert written == []


def test_unknown_clip_id_writes_nothing(written: list) -> None:
    result = run(FakeModel(["emote"], ["Wave_Montage"], []))
    assert result["failure"] == "invalid_pick"
    assert written == []


def test_clip_outside_chosen_categories_writes_nothing(written: list) -> None:
    result = run(FakeModel(["emote"], ["Punch_Jab_Montage"], []))
    assert result["failure"] == "invalid_pick"
    assert written == []


def test_rejection_after_retry_writes_nothing(written: list) -> None:
    model = FakeModel(["emote"], ["Celebration_Montage", "Dance_Loop_Montage"], [False, False])
    result = run(model)
    assert result["failure"] == "rejected"
    assert result["rejected_clip_ids"] == ["Celebration_Montage", "Dance_Loop_Montage"]
    assert written == []


def test_retry_excludes_rejected_clip(written: list) -> None:
    model = FakeModel(["emote"], ["Celebration_Montage", "Crying_Montage"], [False, True])
    run(model)
    _, (_, retry_message) = model.pickers[ClipPick].calls[1]
    assert "Celebration_Montage" not in retry_message
    assert [export.clip_id for export in written] == ["Crying_Montage"]
