import typing
import unittest

from copilot.generated.session_events import (
    PermissionRequestMcp,
    PermissionRequestRead,
    PermissionRequestShell,
    PermissionRequestShellCommand,
    PermissionRequestWrite,
)

from hefajstos.adapters.copilot_event_mapper import (
    MAX_PERMISSION_DETAIL_CHARACTERS,
    MAX_TOOL_RESULT_CHARACTERS,
    describe_read_access,
    map_model,
    map_permission_request,
    map_session_event,
    sdk_setting_value,
)
from hefajstos.services.models.agent_events import (
    AgentError,
    AgentText,
    TokensUsed,
    ToolFinished,
    ToolStarted,
    TurnFinished,
)
from hefajstos.services.models.model_choice import PROVIDER_DEFAULT
from tests.agent_event_fixtures import (
    make_model_info,
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


class TestMapModel(unittest.TestCase):
    def test_keeps_the_id_the_name_and_the_context_window(self) -> None:
        model = map_model(make_model_info(id="gpt-5.4", name="GPT-5.4"))

        self.assertEqual("gpt-5.4", model.id)
        self.assertEqual("GPT-5.4", model.name)
        self.assertEqual(1_000_000, model.context_window_tokens)

    def test_the_reasoning_effort_starts_with_the_providers_default(self) -> None:
        model = map_model(make_model_info(supported_reasoning_efforts=["low", "high"]))

        self.assertEqual(["reasoning_effort"], [s.key for s in model.settings])
        self.assertEqual([PROVIDER_DEFAULT, "low", "high"], model.settings[0].choices)

    def test_a_model_without_reasoning_effort_has_no_effort_setting(self) -> None:
        model = map_model(make_model_info(supported_reasoning_efforts=None))

        self.assertEqual([], model.settings)

    def test_a_long_context_price_adds_the_context_setting(self) -> None:
        model = map_model(make_model_info(long_context=True))

        context = model.settings[-1]
        self.assertEqual("context_tier", context.key)
        self.assertEqual([PROVIDER_DEFAULT, "long_context"], context.choices)

    def test_a_model_without_billing_has_no_context_setting(self) -> None:
        """'auto' comes without billing and without any setting."""
        model = map_model(
            make_model_info(id="auto", billing=None, supported_reasoning_efforts=None)
        )

        self.assertEqual([], model.settings)


class TestSdkSettingValue(unittest.TestCase):
    def test_the_providers_default_is_not_sent(self) -> None:
        value = sdk_setting_value(
            {"reasoning_effort": PROVIDER_DEFAULT}, "reasoning_effort"
        )

        self.assertIsNone(value)

    def test_a_missing_setting_is_not_sent(self) -> None:
        self.assertIsNone(sdk_setting_value({}, "context_tier"))

    def test_a_chosen_value_is_sent_as_it_is(self) -> None:
        value = sdk_setting_value({"reasoning_effort": "high"}, "reasoning_effort")

        self.assertEqual("high", value)


def make_shell_request(**overrides) -> PermissionRequestShell:
    defaults = dict(
        can_offer_session_approval=True,
        commands=[PermissionRequestShellCommand(identifier="ls", read_only=True)],
        full_command_text="ls src",
        has_write_file_redirection=False,
        intention="See what is in src",
        possible_paths=["src"],
        possible_urls=[],
    )
    defaults.update(overrides)
    return PermissionRequestShell(**defaults)  # type: ignore[arg-type]


class TestDescribeReadAccess(unittest.TestCase):
    def test_a_file_read_is_read_only_and_touches_its_path(self) -> None:
        request = PermissionRequestRead(intention="Read", path="config.yaml")

        self.assertEqual((True, ["config.yaml"]), describe_read_access(request))

    def test_a_file_read_prefers_the_resolved_path(self) -> None:
        request = PermissionRequestRead(
            intention="Read", path="config.yaml", resolved_path="/p/config.yaml"
        )

        self.assertEqual((True, ["/p/config.yaml"]), describe_read_access(request))

    def test_a_shell_command_the_cli_calls_read_only_is_read_only(self) -> None:
        self.assertEqual((True, ["src"]), describe_read_access(make_shell_request()))

    def test_one_writing_command_makes_the_whole_line_not_read_only(self) -> None:
        request = make_shell_request(
            commands=[
                PermissionRequestShellCommand(identifier="ls", read_only=True),
                PermissionRequestShellCommand(identifier="rm", read_only=False),
            ]
        )

        is_read_only, _ = describe_read_access(request)

        self.assertFalse(is_read_only)

    def test_a_redirect_into_a_file_is_not_read_only(self) -> None:
        request = make_shell_request(has_write_file_redirection=True)

        is_read_only, _ = describe_read_access(request)

        self.assertFalse(is_read_only)

    def test_a_line_without_commands_is_not_read_only(self) -> None:
        is_read_only, _ = describe_read_access(make_shell_request(commands=[]))

        self.assertFalse(is_read_only)

    def test_uses_resolved_paths_and_adds_the_directory_it_runs_in(self) -> None:
        request = make_shell_request(
            possible_paths=["src", "README.md"],
            resolved_paths={"src": "/etc/src"},
            resolved_working_directory="/etc",
        )

        _, paths = describe_read_access(request)

        self.assertEqual(["/etc/src", "README.md", "/etc"], paths)

    def test_a_write_request_is_not_read_only(self) -> None:
        request = PermissionRequestWrite(
            can_offer_session_approval=True,
            diff="+ x",
            file_name="a.py",
            intention="Edit",
        )

        self.assertEqual((False, []), describe_read_access(request))

    def test_map_permission_request_carries_the_read_access(self) -> None:
        permission = map_permission_request(make_shell_request(), "req-1")

        self.assertTrue(permission.is_read_only)
        self.assertEqual(["src"], permission.paths)
