from hefajstos.protocols.agent_protocol import AgentProtocol
from hefajstos.services.models.commands import (
    CommandNotice,
    CommandResult,
    CommandSource,
    NewSessionStarted,
)

TURN_RUNNING_MESSAGE = "The agent is still working - wait or abort the turn (ctrl+x)."


class NewCommand:
    name = "new"
    description = "Start a new session - the agent forgets the conversation"
    source = CommandSource.BUILT_IN

    def __init__(self, agent_protocol: AgentProtocol) -> None:
        self.agent_protocol = agent_protocol

    async def run(self, arguments: str) -> CommandResult:
        if self.agent_protocol.is_turn_running:
            return CommandNotice(text=TURN_RUNNING_MESSAGE, is_error=True)
        await self.agent_protocol.new_session()
        return NewSessionStarted()
