"""Loads the tracked motion catalog and answers lookups by category and clip id."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict, model_validator

from orchestrator.paths import REPO_ROOT

CATALOG_PATH = REPO_ROOT / "motion_catalog.json"

Category = Literal["attack", "react", "emote", "interact", "cast"]


class CatalogClip(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    clip_id: str
    category: Category
    source_anim: str
    description: str
    demo_tags: tuple[str, ...]


class MotionCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source: str
    categories: tuple[Category, ...]
    clips: tuple[CatalogClip, ...]

    @model_validator(mode="after")
    def check_entries(self) -> MotionCatalog:
        """Rules that span fields, so bad catalog data fails at load rather than mid-graph."""
        if set(self.categories) != set(get_args(Category)):
            raise ValueError("catalog categories do not match the Category type")
        ids = [clip.clip_id for clip in self.clips]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate clip_id in catalog")
        for clip in self.clips:
            # UE plays a clip by matching clip_id to the montage asset name.
            if clip.clip_id != f"{clip.source_anim}_Montage":
                raise ValueError(f"{clip.clip_id} does not match {clip.source_anim}_Montage")
        return self


def load_catalog(path: Path = CATALOG_PATH) -> MotionCatalog:
    return MotionCatalog.model_validate_json(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def get_catalog() -> MotionCatalog:
    """Every caller shares this instance, which is why the models are frozen."""
    return load_catalog()


def categories() -> tuple[Category, ...]:
    return get_catalog().categories


def by_category(category: Category) -> tuple[CatalogClip, ...]:
    return tuple(clip for clip in get_catalog().clips if clip.category == category)


def get(clip_id: str) -> CatalogClip | None:
    for clip in get_catalog().clips:
        if clip.clip_id == clip_id:
            return clip
    return None
