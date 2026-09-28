import typing
import unittest

from copilot.generated.session_events import (
    PermissionRequestMcp,
    PermissionRequestRead,
    PermissionRequestShell,
    PermissionRequestWrite,
)

from hefajstos.adapters.copilot_event_mapper import (
    MAX_PERMISSION_DETAIL_CHARACTERS,
    MAX_TOOL_RESULT_CHARACTERS,
    map_permission_request,
    map_session_event,
)
from hefajstos.services.models.agent_events import (
    AgentError,
    AgentText,
    TokensUsed,
    ToolFinished,
    ToolStarted,
    TurnFinished,
)
from tests.agent_event_fixtures import (
    make_session_error,
    make_session_idle,
    make_text_delta,
    make_text_done,
    make_tool_complete,
    make_tool_failure,
    make_tool_start,
    make_usage,
)


class TestMapSessionEventKnownEvents(unittest.TestCase):
    def test_maps_a_message_chunk_to_agent_text_that_is_not_final(self) -> None:
        event = map_session_event(
            make_text_delta(delta_content="lo ", message_id="msg-9")
        )

        self.assertEqual(
            AgentText(message_id="msg-9", text="lo ", is_final=False), event
        )

    def test_maps_a_full_message_to_final_agent_text(self) -> None:
        event = map_session_event(
            make_text_done(content="Hello there", message_id="msg-9")
        )

        self.assertEqual(
            AgentText(message_id="msg-9", text="Hello there", is_final=True), event
        )

    def test_maps_a_tool_start_to_tool_started(self) -> None:
        event = map_session_event(
            make_tool_start(tool_name="execute", arguments={"command": "ls"})
        )

        self.assertEqual(
            ToolStarted(
                tool_call_id="call-1", tool_name="execute", arguments={"command": "ls"}
            ),
            event,
        )

    def test_maps_a_session_idle_to_turn_finished(self) -> None:
        event = map_session_event(make_session_idle(aborted=True))

        self.assertEqual(TurnFinished(), event)

    def test_maps_a_usage_event_to_tokens_used(self) -> None:
        event = map_session_event(make_usage(input_tokens=1200, output_tokens=340))

        self.assertEqual(TokensUsed(input_tokens=1200, output_tokens=340), event)

    def test_maps_a_session_error_to_agent_error(self) -> None:
        event = map_session_event(make_session_error(message="Too many requests"))

        self.assertEqual(AgentError(message="Too many requests"), event)


class TestMapSessionEventEdgeCases(unittest.TestCase):
    def test_returns_none_for_an_event_type_we_do_not_model(self) -> None:
        unmodelled = make_text_delta()
        unmodelled.data = object()  # type: ignore[assignment]

        self.assertIsNone(map_session_event(unmodelled))

    def test_treats_missing_token_counts_as_zero(self) -> None:
        event = map_session_event(make_usage(input_tokens=None, output_tokens=None))

        self.assertEqual(TokensUsed(input_tokens=0, output_tokens=0), event)

    def test_replaces_non_dict_tool_arguments_with_an_empty_dict(self) -> None:
        event = map_session_event(make_tool_start(arguments="not a dict"))

        self.assertEqual({}, typing.cast(ToolStarted, event).arguments)


class TestMapSessionEventToolResults(unittest.TestCase):
    def test_takes_the_content_from_a_successful_result(self) -> None:
        event = map_session_event(make_tool_complete())

        self.assertEqual(
            ToolFinished(tool_call_id="call-1", success=True, content="README.md"),
            event,
        )

    def test_takes_the_message_from_an_error_instead_of_the_result(self) -> None:
        event = map_session_event(make_tool_failure(message="command not found"))

        self.assertEqual(
            ToolFinished(
                tool_call_id="call-1", success=False, content="command not found"
            ),
            event,
        )

    def test_returns_empty_content_when_there_is_neither_result_nor_error(self) -> None:
        event = map_session_event(make_tool_complete(result=None))

        self.assertEqual("", typing.cast(ToolFinished, event).content)

    def test_shortens_a_result_longer_than_the_limit(self) -> None:
        from copilot.generated.session_events import ToolExecutionCompleteResult

        long_output = "x" * (MAX_TOOL_RESULT_CHARACTERS + 500)

        event = map_session_event(
            make_tool_complete(result=ToolExecutionCompleteResult(content=long_output))
        )

        content = typing.cast(ToolFinished, event).content
        self.assertTrue(content.startswith("x" * MAX_TOOL_RESULT_CHARACTERS))
        self.assertIn("500 more characters", content)


class TestMapPermissionRequest(unittest.TestCase):
    def _make_shell_request(self, **overrides) -> PermissionRequestShell:
        defaults = dict(
            can_offer_session_approval=True,
            commands=[],
            full_command_text="rm -rf build",
            has_write_file_redirection=False,
            intention="Clean the build directory",
            possible_paths=[],
            possible_urls=[],
        )
        defaults.update(overrides)
        return PermissionRequestShell(**defaults)  # type: ignore[arg-type]

    def test_uses_the_full_command_text_as_the_summary_of_a_shell_request(self) -> None:
        permission = map_permission_request(self._make_shell_request(), "req-1")

        self.assertEqual("rm -rf build", permission.summary)
        self.assertEqual("Clean the build directory", permission.detail)
        self.assertEqual("run command", permission.action)
        self.assertEqual("req-1", permission.request_id)

    def test_uses_the_file_name_and_diff_of_a_write_request(self) -> None:
        request = PermissionRequestWrite(
            can_offer_session_approval=True,
            diff="+ new line",
            file_name="src/main.py",
            intention="Add a function",
        )

        permission = map_permission_request(request, "req-2")

        self.assertEqual("src/main.py", permission.summary)
        self.assertEqual("+ new line", permission.detail)

    def test_carries_the_manual_approval_flag_through(self) -> None:
        request = PermissionRequestRead(
            intention="Read the config",
            path="config.yaml",
            managed_approval_required=True,
        )

        permission = map_permission_request(request, "req-3")

        self.assertTrue(permission.requires_manual_approval)

    def test_defaults_the_manual_approval_flag_to_false(self) -> None:
        request = PermissionRequestRead(intention="Read the config", path="config.yaml")

        permission = map_permission_request(request, "req-4")

        self.assertFalse(permission.requires_manual_approval)

    def test_never_arrives_pre_approved(self) -> None:
        permission = map_permission_request(self._make_shell_request(), "req-5")

        self.assertFalse(permission.auto_approved)

    def test_shortens_a_detail_longer_than_the_limit(self) -> None:
        request = PermissionRequestWrite(
            can_offer_session_approval=True,
            diff="+" * (MAX_PERMISSION_DETAIL_CHARACTERS + 100),
            file_name="src/main.py",
            intention="Add a function",
        )

        permission = map_permission_request(request, "req-6")

        self.assertIn("100 more characters", permission.detail)

    def test_falls_back_to_the_class_name_for_a_variant_we_do_not_know(self) -> None:
        class FuturePermissionRequest:
            managed_approval_required = False

        with self.assertLogs(
            "hefajstos.adapters.copilot_event_mapper", level="WARNING"
        ):
            permission = map_permission_request(FuturePermissionRequest(), "req-7")  # type: ignore[arg-type]

        self.assertEqual("FuturePermissionRequest", permission.summary)
        self.assertEqual("unknown action", permission.action)


class TestDescribePermissionRequest(unittest.TestCase):
    def test_names_an_mcp_tool_by_its_server_and_tool(self) -> None:
        request = PermissionRequestMcp(
            args=None,
            read_only=False,
            server_name="github",
            tool_name="create_issue",
            tool_title="Create issue",
        )

        permission = map_permission_request(request, "req-8")

        self.assertEqual("MCP tool", permission.action)
        self.assertEqual("github/create_issue", permission.summary)
        self.assertEqual("Create issue", permission.detail)
