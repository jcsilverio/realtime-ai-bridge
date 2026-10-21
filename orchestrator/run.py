"""CLI: python -m orchestrator.run \"throw a quick jab\""""

from __future__ import annotations

import sys

from dotenv import load_dotenv

from orchestrator.graph import build_graph


def main() -> None:
    load_dotenv()
    intent = (
        " ".join(sys.argv[1:])
        if len(sys.argv) > 1
        else "throw a quick jab"
    )
    app = build_graph()
    result = app.invoke(
        {
            "intent": intent,
            "categories": [],
            "export": None,
            "export_path": None,
            "error": None,
        }
    )
    print(f"Categories: {', '.join(result['categories'])}")
    if result.get("error"):
        print(result["error"])
        raise SystemExit(1)
    export = result["export"]
    print(f"Wrote {result['export_path']}")
    print(f"  source={export.source} clip_id={export.clip_id} request_id={export.request_id}")


if __name__ == "__main__":
    main()
