"""Checks that every catalog clip has a committed montage and sequence."""

import pytest

from orchestrator.catalog import CatalogClip, get_catalog
from orchestrator.paths import REPO_ROOT

INTEGRATION_DEMO = REPO_ROOT / "unreal" / "RealtimeAIBridge" / "Content" / "IntegrationDemo"


@pytest.mark.parametrize("clip", get_catalog().clips, ids=lambda clip: clip.clip_id)
def test_montage_and_sequence_exist(clip: CatalogClip) -> None:
    montage = INTEGRATION_DEMO / f"{clip.clip_id}.uasset"
    sequence = INTEGRATION_DEMO / f"{clip.source_anim}.uasset"
    assert montage.is_file(), f"missing {montage.name}"
    assert sequence.is_file(), f"missing {sequence.name}"
