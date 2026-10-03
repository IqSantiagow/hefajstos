import unittest

from hefajstos.services.commands.new_command import TURN_RUNNING_MESSAGE, NewCommand
from hefajstos.services.models.commands import (
    CommandNotice,
    CommandSource,
    NewSessionStarted,
)


class FakeAgent:
    def __init__(self, is_turn_running: bool = False) -> None:
        self.is_turn_running = is_turn_running
        self.new_sessions = 0

    async def new_session(self) -> None:
        self.new_sessions += 1


class TestNewCommand(unittest.IsolatedAsyncioTestCase):
    async def test_starts_a_new_session(self) -> None:
        agent = FakeAgent()

        result = await NewCommand(agent_protocol=agent).run("")  # type: ignore[arg-type]

        self.assertEqual(NewSessionStarted(), result)
        self.assertEqual(1, agent.new_sessions)

    async def test_refuses_while_the_agent_is_working(self) -> None:
        agent = FakeAgent(is_turn_running=True)

        result = await NewCommand(agent_protocol=agent).run("")  # type: ignore[arg-type]

        self.assertEqual(
            CommandNotice(text=TURN_RUNNING_MESSAGE, is_error=True), result
        )
        self.assertEqual(0, agent.new_sessions)

    def test_is_a_built_in_command_called_new(self) -> None:
        self.assertEqual("new", NewCommand.name)
        self.assertEqual(CommandSource.BUILT_IN, NewCommand.source)
