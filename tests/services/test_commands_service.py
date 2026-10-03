import unittest

from hefajstos.services.commands_service import CommandsService, parse_command_text
from hefajstos.services.models.commands import (
    ClearFeed,
    CommandNotice,
    CommandResult,
    CommandSource,
)


class FakeCommand:
    """Implements CommandProtocol and remembers the arguments it got."""

    def __init__(
        self, name: str, source: CommandSource = CommandSource.BUILT_IN
    ) -> None:
        self.name = name
        self.description = f"the {name} command"
        self.source = source
        self.received_arguments: list[str] = []

    async def run(self, arguments: str) -> CommandResult:
        self.received_arguments.append(arguments)
        return ClearFeed()


class TestParseCommandText(unittest.TestCase):
    def test_splits_the_name_from_the_arguments(self) -> None:
        self.assertEqual(("model", "gpt-5"), parse_command_text("/model gpt-5"))

    def test_a_command_without_arguments_gets_an_empty_string(self) -> None:
        self.assertEqual(("clear", ""), parse_command_text("/clear"))

    def test_surrounding_spaces_and_case_do_not_matter(self) -> None:
        self.assertEqual(("model", "a b"), parse_command_text("  /Model   a b  "))


class TestCommandsServiceList(unittest.TestCase):
    def test_lists_the_commands_that_start_with_the_prefix(self) -> None:
        service = CommandsService([FakeCommand("model"), FakeCommand("clear")])

        names = [command.name for command in service.list_matching("/mo")]

        self.assertEqual(["model"], names)

    def test_a_lone_slash_lists_everything_sorted(self) -> None:
        service = CommandsService([FakeCommand("model"), FakeCommand("clear")])

        names = [command.name for command in service.list_matching("/")]

        self.assertEqual(["clear", "model"], names)

    def test_a_prefix_nothing_starts_with_lists_nothing(self) -> None:
        service = CommandsService([FakeCommand("model")])

        self.assertEqual([], service.list_matching("/xyz"))


class TestCommandsServiceAdd(unittest.TestCase):
    def test_an_extension_cannot_take_a_built_in_name(self) -> None:
        service = CommandsService([FakeCommand("model")])

        with self.assertRaises(ValueError):
            service.add(FakeCommand("model", source=CommandSource.EXTENSION))

    def test_a_new_name_is_added(self) -> None:
        service = CommandsService([])

        service.add(FakeCommand("ask", source=CommandSource.EXTENSION))

        self.assertEqual(["ask"], [c.name for c in service.list_matching("")])


class TestCommandsServiceRun(unittest.IsolatedAsyncioTestCase):
    async def test_runs_the_command_with_its_arguments(self) -> None:
        command = FakeCommand("model")

        result = await CommandsService([command]).run("/model gpt-5")

        self.assertEqual(ClearFeed(), result)
        self.assertEqual(["gpt-5"], command.received_arguments)

    async def test_an_unknown_command_is_an_error_notice(self) -> None:
        result = await CommandsService([]).run("/nope now")

        self.assertEqual(
            CommandNotice(text="Unknown command: /nope", is_error=True), result
        )
