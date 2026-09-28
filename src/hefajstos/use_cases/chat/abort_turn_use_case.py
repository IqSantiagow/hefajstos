from hefajstos.protocols.agent_protocol import AgentProtocol


class AbortTurnUseCase:
    def __init__(self, agent_protocol: AgentProtocol) -> None:
        self.agent_protocol = agent_protocol

    async def __call__(self) -> None:
        await self.agent_protocol.abort_turn()
