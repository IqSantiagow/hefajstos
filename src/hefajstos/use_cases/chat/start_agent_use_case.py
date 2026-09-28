from hefajstos.presentation.view_models.header_view_model import AgentInfoViewModel
from hefajstos.protocols.agent_protocol import AgentProtocol


class StartAgentUseCase:
    def __init__(self, agent_protocol: AgentProtocol) -> None:
        self.agent_protocol = agent_protocol

    async def __call__(self) -> AgentInfoViewModel:
        await self.agent_protocol.start()
        return AgentInfoViewModel.from_agent(
            model=self.agent_protocol.model,
            working_directory=self.agent_protocol.working_directory,
        )
