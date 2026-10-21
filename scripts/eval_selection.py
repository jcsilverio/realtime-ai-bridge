#!/usr/bin/env python3
"""Score the selection graph against the eval cases without writing an export."""

from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from orchestrator.config import MODEL_NAME
from orchestrator.eval_cases import load_cases
from orchestrator.graph import build_graph, initial_state
from orchestrator.schemas import MotionExport


def skip_write(export: MotionExport) -> Path:
    return Path("not written")


def main() -> None:
    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set. Copy .env.example to .env and add your key.")
        raise SystemExit(1)
    cases = load_cases()
    graph = build_graph(writer=skip_write)
    print(f"{MODEL_NAME}, {date.today()}, {len(cases)} cases")

    routed = chosen = should_play = held = should_hold = rejections = 0
    for case in cases:
        result = graph.invoke(initial_state(case.intent))
        played = result["export"].clip_id if result["export"] else None
        rejections += len(result["rejected_clip_ids"])
        if case.acceptable_clip_ids:
            should_play += 1
            routed += bool(set(result["categories"]) & case.expected_categories)
            correct = played in case.acceptable_clip_ids
            chosen += correct
        else:
            should_hold += 1
            correct = played is None
            held += correct
        print(f"{'ok  ' if correct else 'MISS'} {case.intent!r}: {played or 'nothing'}")
        if not correct:
            acceptable = ", ".join(case.acceptable_clip_ids) or "nothing"
            print(f"     categories {', '.join(result['categories'])}, acceptable {acceptable}")
            for detail in (result["error"], result["eval_reason"]):
                if detail:
                    print(f"     {detail}")

    print()
    print(f"Category routing: {routed}/{should_play}")
    print(f"Clip choice: {chosen}/{should_play}")
    print(f"Nothing played when nothing fits: {held}/{should_hold}")
    print(f"Overall: {chosen + held}/{should_play + should_hold}")
    print(f"Evaluator rejections: {rejections}")


if __name__ == "__main__":
    main()
