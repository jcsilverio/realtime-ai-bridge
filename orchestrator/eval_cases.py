"""Loads the selection eval cases and checks every clip id against the catalog."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from orchestrator.catalog import Category, get
from orchestrator.paths import REPO_ROOT

CASES_PATH = REPO_ROOT / "evals" / "selection_cases.jsonl"


class EvalCase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    intent: str = Field(min_length=1)
    # An empty tuple means nothing should play for this intent.
    acceptable_clip_ids: tuple[str, ...]

    @model_validator(mode="after")
    def check_clip_ids(self) -> EvalCase:
        if len(set(self.acceptable_clip_ids)) != len(self.acceptable_clip_ids):
            raise ValueError("duplicate clip id in acceptable_clip_ids")
        for clip_id in self.acceptable_clip_ids:
            if get(clip_id) is None:
                raise ValueError(f"{clip_id} is not in the catalog")
        return self

    @property
    def expected_categories(self) -> set[Category]:
        """Read from the catalog, so a case cannot name a category its clips are not in."""
        return {get(clip_id).category for clip_id in self.acceptable_clip_ids}


def load_cases(path: Path = CASES_PATH) -> tuple[EvalCase, ...]:
    cases = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            cases.append(EvalCase.model_validate_json(line))
        except ValidationError as error:
            # Pydantic's message does not say which line of the file failed.
            raise ValueError(f"{path.name} line {number}: {error}") from error
    intents = [case.intent for case in cases]
    if len(intents) != len(set(intents)):
        raise ValueError(f"duplicate intent in {path.name}")
    return tuple(cases)
