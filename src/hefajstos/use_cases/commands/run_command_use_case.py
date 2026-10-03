import logging

from hefajstos.presentation.view_models.chat_item_view_model import NoticeViewModel
from hefajstos.presentation.view_models.command_view_model import (
    ClearFeedViewModel,
    NewSessionViewModel,
)
from hefajstos.presentation.view_models.model_picker_view_model import (
    ModelPickerViewModel,
)
from hefajstos.protocols.commands_protocol import CommandsProtocol
from hefajstos.services.models.agent_sdk_error import AgentSdkError
from hefajstos.services.models.commands import (
    ClearFeed,
    CommandNotice,
    CommandResult,
    NewSessionStarted,
    OpenModelPicker,
)

logger = logging.getLogger(__name__)

CommandOutcome = (
    NoticeViewModel | ClearFeedViewModel | NewSessionViewModel | ModelPickerViewModel
)


class RunCommandUseCase:
    def __init__(self, commands_protocol: CommandsProtocol) -> None:
        self.commands_protocol = commands_protocol

    async def __call__(self, text: str) -> CommandOutcome:
        try:
            result = await self.commands_protocol.run(text)
        except AgentSdkError as e:
            logger.warning("Command %r failed", text, exc_info=e)
            return NoticeViewModel(content=str(e), is_error=True)
        return build_command_outcome(result)


def build_command_outcome(result: CommandResult) -> CommandOutcome:
    if isinstance(result, ClearFeed):
        return ClearFeedViewModel()
    if isinstance(result, NewSessionStarted):
        return NewSessionViewModel.started()
    if isinstance(result, OpenModelPicker):
        return ModelPickerViewModel.from_result(result)
    if isinstance(result, CommandNotice):
        return NoticeViewModel(content=result.text, is_error=result.is_error)
    raise TypeError(f"Unknown command result {type(result).__name__}")
