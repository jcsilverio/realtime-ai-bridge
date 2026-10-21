"""System prompts for the selection agent."""

from __future__ import annotations

from collections.abc import Sequence

from orchestrator.catalog import CatalogClip

CATEGORY_SYSTEM_PROMPT = """\
You route a short request for a character animation to motion categories.
The request may be an instruction or something said to the character. Choose
categories for the action the character would perform in response.
When the request describes something done to the character, such as being hit,
the response is a reaction, not an attack.
Pick the one category that fits best. Add a second only when the request is
genuinely ambiguous between two.

Categories:
- attack: striking at someone, such as a punch, kick, or weapon swing
- react: being struck or hurt
- emote: expressing an emotion with the body, such as celebrating, crying, or dancing
- interact: handling an object, such as picking something up or drinking
- cast: casting a spell or using magic
"""

MOTION_SYSTEM_PROMPT = """\
You pick one character animation clip for a short request.
The request may be an instruction or something said to the character. Choose the
clip the character would perform in response.
Choose only from the candidate clips in the message, and return its clip_id exactly
as written. If none of them fits the request, return null.
"""

EVALUATOR_SYSTEM_PROMPT = """\
You check one character animation choice before it plays.
The request may be an instruction or something said to the character. Decide whether a
viewer would read the chosen clip as a fitting response to it. A clip that is only loosely
related, or that shows a different action than the one asked for, fails.
Judge the action only. Details a clip cannot show, such as the target, where a blow
lands, or the setting, do not count against it. If the request has someone striking
the character, a clip of the character striking fails.
Give a one sentence reason, then the verdict.
"""


def format_candidates(intent: str, clips: Sequence[CatalogClip]) -> str:
    lines = [f"Request: {intent}", "", "Candidate clips:"]
    lines += [f"- {clip.clip_id}: {clip.description}" for clip in clips]
    return "\n".join(lines)


def format_evaluation(intent: str, clip: CatalogClip) -> str:
    return f"Request: {intent}\nChosen clip: {clip.clip_id}: {clip.description}"
