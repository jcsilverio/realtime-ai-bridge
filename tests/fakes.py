"""Scripted stand-in for the chat model, shared by the graph and MCP server tests.

Pytest only collects test_*.py files, so this module is a plain helper. It imports as
fakes because tests/ has no __init__.py and pytest puts the folder on sys.path.
"""

from orchestrator.graph import CategoryPick, ClipPick, EvalVerdict


class ScriptedPicker:
    def __init__(self, replies: list) -> None:
        self.replies = list(replies)
        self.calls: list = []

    def invoke(self, messages: list) -> object:
        self.calls.append(messages)
        # An unscripted extra call raises IndexError, which is how tests catch a missed retry limit.
        return self.replies.pop(0)


class FakeModel:
    """Returns scripted replies per output schema.

    LangChain's fake chat models do not implement with_structured_output.
    """

    def __init__(
        self, categories: list[str], clips: list[str | None], verdicts: list[bool]
    ) -> None:
        self.pickers = {
            CategoryPick: ScriptedPicker([CategoryPick(categories=categories)]),
            ClipPick: ScriptedPicker([ClipPick(clip_id=clip_id) for clip_id in clips]),
            EvalVerdict: ScriptedPicker(
                [EvalVerdict(reason="scripted", passed=p) for p in verdicts]
            ),
        }

    def with_structured_output(self, schema: type) -> ScriptedPicker:
        return self.pickers[schema]
