"""Tests for the selection prompts."""

from typing import get_args

from orchestrator.catalog import Category
from orchestrator.prompts import CATEGORY_SYSTEM_PROMPT


def test_category_prompt_describes_every_category() -> None:
    for category in get_args(Category):
        assert f"- {category}:" in CATEGORY_SYSTEM_PROMPT, category
