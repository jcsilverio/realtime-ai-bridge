# realtime-ai-bridge

[![CI](https://github.com/jcsilverio/realtime-ai-bridge/actions/workflows/ci.yml/badge.svg)](https://github.com/jcsilverio/realtime-ai-bridge/actions/workflows/ci.yml)

Type a request like "throw a quick jab" and an Unreal Engine 5 character plays it.
A LangGraph agent picks a clip from a catalog of 11 animations across five
categories (attack, react, emote, interact, and cast) and writes its choice to a JSON
file. The UE 5.4 project picks up that file and plays the matching montage. If
nothing in the catalog fits, nothing plays.

![Three typed requests make the Unreal character cast a spell, dance, and drink](docs/images/hero.gif)

No API key? A keyword stub runs the same path for a few clips.

## How it works

Requests come from the command line or from an MCP client, and both go through
the same graph.

```mermaid
flowchart TD
    A[CLI or MCP play_motion] --> B[select_categories]
    B --> C[select_motion]
    C -->|no fit or bad pick| X[nothing written]
    C --> D[evaluate]
    D -->|reject, retry once| C
    D -->|reject twice| X
    D -->|pass| E[write exports/latest.json]
    E --> F[UE consumer polls and plays the montage]
```

The agent picks in two steps. First it narrows the request to one or two
categories, then it chooses a clip from those, or says none fits. A separate call
checks that choice against the request. If it's rejected, the agent gets one more
try with that clip taken out. Python validates every answer along the way, so a
clip name the model made up never reaches Unreal.

On the Unreal side, a component on the character reads the file twice a second
and plays the montage whose name matches `clip_id`. Each `request_id` plays once,
and anything it doesn't recognize is ignored. Idle and locomotion stay on the
Animation Blueprint.

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

`ThirdPersonMap` opens by default. Press Play, then run this from the repo root:

```powershell
.\.venv\Scripts\python.exe -m orchestrator.run "we won the championship!"
```

```text
Categories: emote
Evaluator: The triumphant celebration with arms raised clearly matches a championship win reaction.
Wrote exports\latest.json
  source=agent clip_id=Celebration_Montage request_id=031786a1-f57e-464d-9824-acaee5dbd29f
```

Within half a second the character throws its arms up in celebration, then blends
back to idle. This is the file it read:

```json
{
  "request_id": "031786a1-f57e-464d-9824-acaee5dbd29f",
  "source": "agent",
  "clip_id": "Celebration_Montage",
  "metadata": {
    "intent": "we won the championship!",
    "categories": "emote"
  }
}
```

The command is in [`orchestrator/run.py`](orchestrator/run.py), the graph in
[`orchestrator/graph.py`](orchestrator/graph.py), and the file is written by
[`orchestrator/export_writer.py`](orchestrator/export_writer.py).

When nothing fits, nothing is written:

```text
> .\.venv\Scripts\python.exe -m orchestrator.run "file my taxes"
Categories: interact
No clip fits intent: 'file my taxes'
> $LASTEXITCODE
2
```

The category step always returns at least one category, so the refusal comes from the
clip step, which looks at the two interact clips and picks neither. `exports/latest.json`
still holds the celebration afterwards, so Unreal has nothing new to play.

More requests to try. None of them names a clip, so the keyword stub can't handle
them, but the agent maps each one to a category and a clip:

| Request | Category | Clip |
|---|---|---|
| "sock him in the jaw" | attack | `Punch_Jab_Montage` |
| "the brute decks you right in the face" | react | `Hit_Head_Montage` |
| "bust a move" | emote | `Dance_Loop_Montage` |
| "there's a coin on the table in front of you" | interact | `PickUp_Table_Montage` |
| "hurl a fireball at the goblin" | cast | `Spell_Simple_Shoot_Montage` |

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

## The export file

`exports/latest.json` is the only thing Python and Unreal share. Its shape is
`MotionExport` in [`orchestrator/schemas.py`](orchestrator/schemas.py):

| Field | Read by Unreal | Purpose |
|---|---|---|
| `request_id` | Yes | New for every export. Each one plays once. |
| `clip_id` | Yes | The montage asset name under `Content/IntegrationDemo/`. |
| `source` | No | `agent` or `stub`, whichever wrote the file. |
| `metadata` | No | Strings for logging, such as the original request. |

The model rejects any other field, so a misspelled field fails in Python instead of
being silently skipped in Unreal. Playback settings like blend times live on each
montage asset, not in the file. On the Unreal side, a missing file, JSON it can't
read, or an unknown `clip_id` does nothing.

Anything that writes this shape can drive the character. The keyword stub does, and
so does copying the tracked sample over the live file with PIE running:

```powershell
Copy-Item exports\samples\jab_stub.json exports\latest.json
```

Over MCP, `motion://contract` serves the same schema, generated from the model.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The tests use a scripted fake model, so no key is needed. CI runs them on
every push to `main` and on pull requests. Besides the graph tests, they check
that the catalog loads and follows its naming rule, and that every catalog clip
has its montage and sequence committed under `Content/IntegrationDemo/`. A clip
id with no matching asset fails the build instead of doing nothing in UE.

## Evaluation

`scripts/eval_selection.py` runs the 26 requests in `evals/selection_cases.jsonl`
through the real graph without writing an export. Six of them should play nothing.

```powershell
.\.venv\Scripts\python.exe scripts\eval_selection.py
```

The script needs an API key, so it runs locally and not in CI.
Results with `gpt-5.4-mini` at low reasoning effort, Oct. 2026:

| Run | Category routing | Clip choice | Nothing played when nothing fits | Overall |
|---|---|---|---|---|
| 1 | 20/20 | 20/20 | 6/6 | 26/26 |
| 2 | 20/20 | 20/20 | 6/6 | 26/26 |
| 3 | 19/20 | 19/20 | 6/6 | 25/26 |

The one miss was "you look thirsty", which went to emote instead of interact, so
nothing played. These runs follow one prompt change made after two earlier runs
scored 25/26 and 23/26. That change was checked on these same 26 cases, so the
numbers show the prompts fit this set, not how they would do on new requests.

## Use from an MCP client

`mcp_server/server.py` runs the same graph as the CLI as an MCP server over stdio.

- `motion://catalog` is a resource with every clip, its category, and its description.
- `motion://contract` is a resource with the JSON schema of the export Unreal reads.
- `list_motions` is a tool that lists clips, optionally for one category.
- `play_motion` is a tool that runs a request through the selection graph. When
nothing fits or the evaluator rejects the pick, it returns the reason and writes
nothing.

To connect a client, point it at the venv's Python with the server script as its
argument. Most clients take a JSON entry like this one, though the file name and the
top-level key vary by client:

```json
{
  "mcpServers": {
    "realtime-ai-bridge": {
      "command": "C:\\path\\to\\realtime-ai-bridge\\.venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\realtime-ai-bridge\\mcp_server\\server.py"]
    }
  }
}
```

The server reads the key from `.env` in the repo root, the same as the CLI. With PIE
running, ask the agent what the character can do, then ask for a move.

`tests/test_mcp_stdio.py` starts the server and calls it over stdio the same way a
client does, so the tests check the server without any client installed.

## Credits and license

- Code: MIT, see [LICENSE](LICENSE).
- Animation: [Quaternius Universal Animation Library](https://quaternius.com/packs/universalanimationlibrary.html) (CC0), retargeted to the UE5 mannequin under
`unreal/RealtimeAIBridge/Content/IntegrationDemo/`.
- Third Person template content and mannequin: Epic Games, under the Unreal
Engine EULA.
