"""Tests for the selection prompts."""

from typing import get_args

from orchestrator.catalog import Category, by_category
from orchestrator.prompts import CATEGORY_SYSTEM_PROMPT, format_candidates


def test_category_prompt_describes_every_category() -> None:
    for category in get_args(Category):
        assert f"- {category}:" in CATEGORY_SYSTEM_PROMPT, category


def test_candidates_list_every_clip() -> None:
    clips = by_category("react")
    text = format_candidates("ouch", clips)
    for clip in clips:
        assert f"- {clip.clip_id}:" in text, clip.clip_id
