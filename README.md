# realtime-ai-bridge

[![CI](https://github.com/jcsilverio/realtime-ai-bridge/actions/workflows/ci.yml/badge.svg)](https://github.com/jcsilverio/realtime-ai-bridge/actions/workflows/ci.yml)

A text request goes in, and an Unreal Engine 5 character plays a matching
animation. A LangGraph agent picks a category and then a clip from a
tracked catalog of 11 clips across 5 categories, and an evaluator checks the
pick before anything is written.

The result is a typed JSON export that a UE 5.4 project polls and plays as a montage on the mannequin. This is routing over a fixed set of committed clips. When nothing fits, nothing is written, and UE ignores any export it doesn't recognize.

A keyword stub covers the same path without an API key.

## Requirements

- Unreal Engine 5.4
- Python 3.14
- An OpenAI API key for the agent path. The keyword stub and the tests run without one.

Tested on Windows 11.

## Setup

```powershell
git clone https://github.com/jcsilverio/realtime-ai-bridge.git
cd realtime-ai-bridge
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Put your key after `OPENAI_API_KEY=` in `.env`.

Open `unreal/RealtimeAIBridge/RealtimeAIBridge.uproject` in Unreal Engine 5.4.

The project is Blueprint only, so there's nothing to compile. The JSON Blueprint Utilities plugin is already enabled. The first open on a new machine compiles shaders and can take several minutes.

## Run

`ThirdPersonMap` opens by default. Press Play, then run from the repo root.

```powershell
.\.venv\Scripts\python.exe -m orchestrator.run "that's terrible news"
```

It prints the categories the agent chose, the evaluator's one-sentence reason,
and the `clip_id` and `request_id` it wrote to `exports/latest.json`. The
character plays that clip within about half a second, then blends back to idle.

Other requests to try:

- "throw a quick jab"
- "we won the championship!"
- "you look thirsty"
- "cast a fireball"
- "file my taxes" (no clip fits, so nothing is written and the command exits 2)

### Without an API key

```powershell
.\.venv\Scripts\python.exe scripts\smoke_stub.py "throw a quick jab"
```

Without an API key, the stub uses keyword matching only: "jab" or "punch" plays the jab,
"celebrate", "victory" or "cheer" plays the celebration, and "dance", "groove" or "boogie" plays the
dance.
Exits 1 when no keyword matches.

### Exit codes

| Code | Meaning |
|---|---|
| 0 | Export written |
| 1 | Error, such as a missing `OPENAI_API_KEY` or a failed API call |
| 2 | No catalog clip fits the request. Nothing written |
| 3 | The model picked a clip outside the candidates it was shown. Nothing written |
| 4 | The evaluator rejected the pick and the one retry. Nothing written |

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The tests use a scripted fake model, so no key is needed. CI runs them on
every push to `main` and on pull requests. Besides the graph tests, they check
that the catalog loads and follows its naming rule, and that every catalog clip
has its montage and sequence committed under `Content/IntegrationDemo/`. A clip
id with no matching asset fails the build instead of doing nothing in UE.

## Credits and license

- Code: MIT, see [LICENSE](LICENSE).
- Animation: [Quaternius Universal Animation Library](https://quaternius.com/packs/universalanimationlibrary.html) (CC0), retargeted to the UE5 mannequin under
  `unreal/RealtimeAIBridge/Content/IntegrationDemo/`.
- Third Person template content and mannequin: Epic Games, under the Unreal
  Engine EULA.
