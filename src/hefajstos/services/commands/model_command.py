from hefajstos.protocols.agent_protocol import AgentProtocol
from hefajstos.services.models.commands import (
    CommandResult,
    CommandSource,
    OpenModelPicker,
)


class ModelCommand:
    name = "model"
    description = "Switch the model, its reasoning effort and context"
    source = CommandSource.BUILT_IN

    def __init__(self, agent_protocol: AgentProtocol) -> None:
        self.agent_protocol = agent_protocol

    async def run(self, arguments: str) -> CommandResult:
        return OpenModelPicker(
            models=await self.agent_protocol.list_models(),
            current_model_id=self.agent_protocol.model,
            current_settings=dict(self.agent_protocol.model_settings),
        )
