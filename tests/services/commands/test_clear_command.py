import unittest

from hefajstos.services.commands.clear_command import ClearCommand
from hefajstos.services.models.commands import ClearFeed, CommandSource


class TestClearCommand(unittest.IsolatedAsyncioTestCase):
    async def test_asks_to_clear_the_feed(self) -> None:
        self.assertEqual(ClearFeed(), await ClearCommand().run(""))

    def test_is_a_built_in_command_called_clear(self) -> None:
        self.assertEqual("clear", ClearCommand.name)
        self.assertEqual(CommandSource.BUILT_IN, ClearCommand.source)
