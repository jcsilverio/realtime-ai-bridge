"""Tests for the motion catalog loader."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from orchestrator.catalog import CATALOG_PATH, by_category, categories, get, load_catalog


@pytest.fixture
def catalog_data() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def write_catalog(folder: Path, data: dict) -> Path:
    path = folder / "motion_catalog.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_tracked_catalog_loads() -> None:
    catalog = load_catalog()
    assert catalog.clips


def test_every_category_has_clips() -> None:
    for category in categories():
        assert by_category(category), category


def test_get_known_id() -> None:
    clip = get("Punch_Jab_Montage")
    assert clip is not None
    assert clip.category == "attack"


def test_get_unknown_id_returns_none() -> None:
    assert get("Wave_Montage") is None


def test_duplicate_clip_id_fails(tmp_path: Path, catalog_data: dict) -> None:
    catalog_data["clips"].append(catalog_data["clips"][0])
    with pytest.raises(ValidationError, match="duplicate clip_id"):
        load_catalog(write_catalog(tmp_path, catalog_data))


def test_unknown_category_fails(tmp_path: Path, catalog_data: dict) -> None:
    catalog_data["clips"][0]["category"] = "wave"
    with pytest.raises(ValidationError, match="unknown category"):
        load_catalog(write_catalog(tmp_path, catalog_data))


def test_clip_id_must_match_source_anim(tmp_path: Path, catalog_data: dict) -> None:
    catalog_data["clips"][0]["clip_id"] = "Jab_Montage"
    with pytest.raises(ValidationError, match="does not match"):
        load_catalog(write_catalog(tmp_path, catalog_data))


def test_extra_field_fails(tmp_path: Path, catalog_data: dict) -> None:
    catalog_data["clips"][0]["play_rate"] = 1.0
    with pytest.raises(ValidationError, match="Extra inputs"):
        load_catalog(write_catalog(tmp_path, catalog_data))