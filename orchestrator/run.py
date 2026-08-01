"""CLI: python -m orchestrator.run \"make the character wave hello\""""

from __future__ import annotations

import sys

from orchestrator.graph import build_graph


def main() -> None:
    intent = (
        " ".join(sys.argv[1:])
        if len(sys.argv) > 1
        else "make the character wave hello"
    )
    app = build_graph()
    result = app.invoke(
        {
            "intent": intent,
            "export": None,
            "export_path": None,
            "error": None,
        }
    )
    if result.get("error"):
        print(result["error"])
        raise SystemExit(1)
    export = result["export"]
    print(f"Wrote {result['export_path']}")
    print(f"  source={export.source} clip_id={export.clip_id} request_id={export.request_id}")


if __name__ == "__main__":
    main()