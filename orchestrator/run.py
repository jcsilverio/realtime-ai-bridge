"""CLI: python -m orchestrator.run \"throw a quick jab\""""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

from orchestrator.graph import Failure, build_graph, initial_state

# Exit 1 stays reserved for unhandled errors such as a failed API call.
EXIT_CODES: dict[Failure, int] = {"no_fit": 2, "invalid_pick": 3, "rejected": 4}


def main() -> None:
    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set. Copy .env.example to .env and add your key.")
        raise SystemExit(1)
    intent = (
        " ".join(sys.argv[1:])
        if len(sys.argv) > 1
        else "throw a quick jab"
    )
    result = build_graph().invoke(initial_state(intent))
    print(f"Categories: {', '.join(result['categories'])}")
    for clip_id in result["rejected_clip_ids"]:
        print(f"Rejected: {clip_id}")
    if result["eval_reason"]:
        print(f"Evaluator: {result['eval_reason']}")
    if result["failure"]:
        print(result["error"])
        raise SystemExit(EXIT_CODES[result["failure"]])
    export = result["export"]
    print(f"Wrote {result['export_path']}")
    print(f"  source={export.source} clip_id={export.clip_id} request_id={export.request_id}")


if __name__ == "__main__":
    main()
