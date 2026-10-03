import unittest

from hefajstos.presentation.view_models.chat_item_view_model import NoticeViewModel
from hefajstos.presentation.view_models.command_view_model import (
    ClearFeedViewModel,
    CommandViewModel,
)
from hefajstos.presentation.view_models.model_picker_view_model import (
    ModelChangedViewModel,
    ModelPickerViewModel,
)
from hefajstos.services.models.agent_sdk_error import AgentSdkError
from hefajstos.services.models.commands import (
    ClearFeed,
    CommandNotice,
    CommandResult,
    CommandSource,
    OpenModelPicker,
)
from hefajstos.services.models.model_choice import ModelChoice, ModelSelection
from hefajstos.use_cases.commands.change_model_use_case import ChangeModelUseCase
from hefajstos.use_cases.commands.list_commands_use_case import ListCommandsUseCase
from hefajstos.use_cases.commands.run_command_use_case import RunCommandUseCase


class FakeCommand:
    def __init__(self, name: str) -> None:
        self.name = name
        self.description = f"the {name} command"
        self.source = CommandSource.BUILT_IN

    async def run(self, arguments: str) -> CommandResult:
        return ClearFeed()


class FakeCommands:
    """Implements CommandsProtocol with one canned result (or failure)."""

    def __init__(
        self,
        result: CommandResult | None = None,
        failure: Exception | None = None,
    ) -> None:
        self.result = result or ClearFeed()
        self.failure = failure
        self.prefixes: list[str] = []
        self.texts: list[str] = []

    def list_matching(self, prefix: str) -> list[FakeCommand]:
        self.prefixes.append(prefix)
        return [FakeCommand("model")]

    async def run(self, text: str) -> CommandResult:
        self.texts.append(text)
        if self.failure is not None:
            raise self.failure
        return self.result


class FakeAgent:
    """The part of AgentProtocol that a model change uses."""

    def __init__(self, failure: Exception | None = None) -> None:
        self.model = "gpt-5"
        self.model_settings: dict[str, str] = {}
        self.working_directory = "/opt/project"
        self.failure = failure

    async def list_models(self) -> list[ModelChoice]:
        return []

    async def set_model(self, selection: ModelSelection) -> None:
        if self.failure is not None:
            raise self.failure
        self.model = selection.model_id
        self.model_settings = selection.settings


def make_list_commands(commands: FakeCommands) -> ListCommandsUseCase:
    return ListCommandsUseCase(commands_protocol=commands)  # type: ignore[arg-type]


def make_run_command(commands: FakeCommands) -> RunCommandUseCase:
    return RunCommandUseCase(commands_protocol=commands)  # type: ignore[arg-type]


def make_change_model(agent: FakeAgent) -> ChangeModelUseCase:
    return ChangeModelUseCase(agent_protocol=agent)  # type: ignore[arg-type]


class TestListCommandsUseCase(unittest.TestCase):
    def test_turns_the_matching_commands_into_view_models(self) -> None:
        commands = FakeCommands()

        rows = make_list_commands(commands)("/mo")

        self.assertEqual(["/mo"], commands.prefixes)
        self.assertEqual(
            [CommandViewModel("model", "the model command", "built-in")], rows
        )


class TestRunCommandUseCase(unittest.IsolatedAsyncioTestCase):
    async def test_passes_the_whole_text_to_the_commands(self) -> None:
        commands = FakeCommands()

        await make_run_command(commands)("/model gpt-5")

        self.assertEqual(["/model gpt-5"], commands.texts)

    async def test_clear_feed_becomes_its_view_model(self) -> None:
        outcome = await make_run_command(FakeCommands(result=ClearFeed()))("/clear")

        self.assertEqual(ClearFeedViewModel(), outcome)

    async def test_a_notice_keeps_its_text_and_error_flag(self) -> None:
        notice = CommandNotice(text="Unknown command: /x", is_error=True)

        outcome = await make_run_command(FakeCommands(result=notice))("/x")

        self.assertEqual(
            NoticeViewModel(content="Unknown command: /x", is_error=True), outcome
        )

    async def test_the_model_picker_becomes_its_view_model(self) -> None:
        picker = OpenModelPicker(
            models=[], current_model_id="gpt-5", current_settings={}
        )

        outcome = await make_run_command(FakeCommands(result=picker))("/model")

        self.assertIsInstance(outcome, ModelPickerViewModel)

    async def test_an_agent_sdk_error_becomes_an_error_notice(self) -> None:
        failure = AgentSdkError("Could not list the models: offline")

        outcome = await make_run_command(FakeCommands(failure=failure))("/model")

        self.assertEqual(
            NoticeViewModel(
                content="Could not list the models: offline", is_error=True
            ),
            outcome,
        )


class TestChangeModelUseCase(unittest.IsolatedAsyncioTestCase):
    async def test_switches_the_agent_to_the_selection(self) -> None:
        agent = FakeAgent()

        await make_change_model(agent)(
            ModelSelection(model_id="claude-sonnet-5", settings={})
        )

        self.assertEqual("claude-sonnet-5", agent.model)

    async def test_the_footer_and_the_notice_show_the_new_model(self) -> None:
        outcome = await make_change_model(FakeAgent())(
            ModelSelection(
                model_id="claude-sonnet-5",
                settings={"reasoning_effort": "high", "context_tier": "default"},
            )
        )

        assert isinstance(outcome, ModelChangedViewModel)
        self.assertEqual("claude-sonnet-5", outcome.agent_info.model)
        self.assertEqual(["high"], outcome.agent_info.model_settings)
        self.assertEqual("/opt/project", outcome.agent_info.working_directory)
        self.assertEqual(
            NoticeViewModel(content="Model: claude-sonnet-5 · high", is_error=False),
            outcome.notice,
        )

    async def test_a_failed_switch_becomes_an_error_notice(self) -> None:
        agent = FakeAgent(failure=AgentSdkError("Could not switch to nope: unknown"))

        outcome = await make_change_model(agent)(
            ModelSelection(model_id="nope", settings={})
        )

        self.assertEqual(
            NoticeViewModel(content="Could not switch to nope: unknown", is_error=True),
            outcome,
        )
        self.assertEqual("gpt-5", agent.model)
