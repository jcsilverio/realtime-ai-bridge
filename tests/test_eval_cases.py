"""Tests for the selection eval cases loader."""

from pathlib import Path

import pytest

from orchestrator.eval_cases import EvalCase, load_cases

NO_FIT = '{"intent": "file my taxes", "acceptable_clip_ids": []}'


def write_cases(folder: Path, *lines: str) -> Path:
    path = folder / "selection_cases.jsonl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def find(intent: str) -> EvalCase:
    return next(case for case in load_cases() if case.intent == intent)


def test_tracked_cases_load() -> None:
    assert load_cases()


def test_unknown_clip_id_names_the_line(tmp_path: Path) -> None:
    bad = '{"intent": "wave hello", "acceptable_clip_ids": ["Wave_Montage"]}'
    # A valid first line proves the number is the real line, not a counter stuck at 1.
    with pytest.raises(ValueError, match="line 2") as caught:
        load_cases(write_cases(tmp_path, NO_FIT, bad))
    assert "Wave_Montage is not in the catalog" in str(caught.value)


def test_duplicate_intent_fails(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="duplicate intent"):
        load_cases(write_cases(tmp_path, NO_FIT, NO_FIT))


def test_extra_field_fails(tmp_path: Path) -> None:
    old_shape = '{"intent": "wave hello", "acceptable_clip_ids": [], "should_reject": true}'
    with pytest.raises(ValueError, match="Extra inputs"):
        load_cases(write_cases(tmp_path, old_shape))


def test_expected_categories_come_from_catalog() -> None:
    assert find("fight him").expected_categories == {"attack"}
    assert find("file my taxes").expected_categories == set()
