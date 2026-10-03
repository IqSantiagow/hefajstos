import logging

from hefajstos.presentation.view_models.chat_item_view_model import NoticeViewModel
from hefajstos.presentation.view_models.footer_view_model import (
    AgentInfoViewModel,
    describe_model_settings,
)
from hefajstos.presentation.view_models.model_picker_view_model import (
    ModelChangedViewModel,
)
from hefajstos.protocols.agent_protocol import AgentProtocol
from hefajstos.services.models.agent_sdk_error import AgentSdkError
from hefajstos.services.models.model_choice import ModelSelection

logger = logging.getLogger(__name__)


class ChangeModelUseCase:
    def __init__(self, agent_protocol: AgentProtocol) -> None:
        self.agent_protocol = agent_protocol

    async def __call__(
        self, selection: ModelSelection
    ) -> ModelChangedViewModel | NoticeViewModel:
        try:
            await self.agent_protocol.set_model(selection)
        except AgentSdkError as e:
            logger.warning("Model change failed", exc_info=e)
            return NoticeViewModel(content=str(e), is_error=True)

        model_settings = describe_model_settings(self.agent_protocol.model_settings)
        return ModelChangedViewModel(
            agent_info=AgentInfoViewModel(
                model=self.agent_protocol.model,
                working_directory=self.agent_protocol.working_directory,
                model_settings=model_settings,
            ),
            notice=NoticeViewModel(
                content=" · ".join(
                    [f"Model: {self.agent_protocol.model}", *model_settings]
                ),
                is_error=False,
            ),
        )
