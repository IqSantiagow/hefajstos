import unittest

from hefajstos.presentation.view_models.chat_item_view_model import (
    AgentTextViewModel,
    NoticeViewModel,
    ToolCallViewModel,
    ToolResultViewModel,
    build_chat_item,
    summarize_tool_arguments,
)
from hefajstos.services.models.agent_events import (
    AgentError,
    AgentText,
    PermissionRequested,
    TokensUsed,
    ToolFinished,
    ToolStarted,
    TurnFinished,
)


def make_permission(**overrides) -> PermissionRequested:
    defaults = dict(
        request_id="req-1",
        action="run command",
        summary="ls",
        detail="",
        requires_manual_approval=False,
    )
    defaults.update(overrides)
    return PermissionRequested(**defaults)  # type: ignore[arg-type]


class TestBuildChatItemText(unittest.TestCase):
    def test_a_chunk_is_not_final(self) -> None:
        item = build_chat_item(AgentText(message_id="m1", text="Cze", is_final=False))

        self.assertEqual(
            AgentTextViewModel(message_id="m1", text="Cze", is_final=False), item
        )

    def test_a_complete_message_is_final(self) -> None:
        item = build_chat_item(AgentText(message_id="m1", text="Hello", is_final=True))

        self.assertEqual(
            AgentTextViewModel(message_id="m1", text="Hello", is_final=True), item
        )


class TestBuildChatItemTools(unittest.TestCase):
    def test_keeps_the_tool_name_and_picks_the_argument(self) -> None:
        item = build_chat_item(
            ToolStarted(
                tool_call_id="c1", tool_name="execute", arguments={"command": "ls -la"}
            )
        )

        self.assertEqual(
            ToolCallViewModel(tool_call_id="c1", title="execute", summary="ls -la"),
            item,
        )

    def test_a_failed_tool_becomes_an_error_result(self) -> None:
        item = build_chat_item(
            ToolFinished(tool_call_id="c1", success=False, content="boom")
        )

        self.assertEqual(
            ToolResultViewModel(tool_call_id="c1", content="boom", is_error=True), item
        )

    def test_a_successful_tool_is_not_an_error(self) -> None:
        item = build_chat_item(
            ToolFinished(tool_call_id="c1", success=True, content="ok")
        )

        self.assertEqual(
            ToolResultViewModel(tool_call_id="c1", content="ok", is_error=False), item
        )


class TestBuildChatItemNotices(unittest.TestCase):
    def test_an_auto_approved_request_becomes_a_notice(self) -> None:
        item = build_chat_item(make_permission(auto_approved=True))

        self.assertFalse(item.is_error)
        self.assertIn("Auto-approved", item.content)
        self.assertIn("ls", item.content)

    def test_a_pending_request_is_not_rendered_as_a_notice(self) -> None:
        self.assertIsNone(build_chat_item(make_permission(auto_approved=False)))

    def test_an_error_becomes_an_error_entry(self) -> None:
        item = build_chat_item(AgentError(message="rate limit"))

        self.assertEqual(NoticeViewModel(content="rate limit", is_error=True), item)


class TestBuildChatItemFiltering(unittest.TestCase):
    def test_events_the_feed_does_not_show_are_filtered_out_here(self) -> None:
        not_rendered = [
            TurnFinished(),
            TokensUsed(input_tokens=1, output_tokens=1),
        ]

        for event in not_rendered:
            self.assertIsNone(
                build_chat_item(event), f"{event} should not reach the feed"
            )


class TestSummarizeToolArguments(unittest.TestCase):
    def test_prefers_the_command_over_anything_else(self) -> None:
        summary = summarize_tool_arguments({"path": "/tmp", "command": "ls"})

        self.assertEqual("ls", summary)

    def test_falls_back_to_the_next_argument_on_the_list(self) -> None:
        self.assertEqual("/tmp/x.py", summarize_tool_arguments({"path": "/tmp/x.py"}))

    def test_returns_an_empty_string_when_there_are_no_arguments(self) -> None:
        self.assertEqual("", summarize_tool_arguments({}))

    def test_falls_back_to_compact_json_for_unknown_arguments(self) -> None:
        self.assertEqual('{"depth":3}', summarize_tool_arguments({"depth": 3}))

    def test_ignores_a_blank_value(self) -> None:
        self.assertEqual(
            '{"command":"   "}', summarize_tool_arguments({"command": "   "})
        )
