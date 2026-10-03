from collections.abc import AsyncGenerator

from hefajstos.presentation.view_models.chat_item_view_model import NoticeViewModel
from hefajstos.presentation.view_models.command_view_model import CommandViewModel
from hefajstos.presentation.view_models.footer_view_model import AgentInfoViewModel
from hefajstos.presentation.view_models.model_picker_view_model import (
    ModelChangedViewModel,
)
from hefajstos.services.models.agent_events import PermissionDecision
from hefajstos.services.models.model_choice import ModelSelection
from hefajstos.use_cases.chat.abort_turn_use_case import AbortTurnUseCase
from hefajstos.use_cases.chat.answer_permission_use_case import (
    AnswerPermissionUseCase,
)
from hefajstos.use_cases.chat.send_message_use_case import SendMessageUseCase
from hefajstos.use_cases.chat.shutdown_agent_use_case import ShutdownAgentUseCase
from hefajstos.use_cases.chat.start_agent_use_case import StartAgentUseCase
from hefajstos.use_cases.chat.stream_agent_responses_use_case import (
    AgentStreamItem,
    StreamAgentResponsesUseCase,
)
from hefajstos.use_cases.commands.change_model_use_case import ChangeModelUseCase
from hefajstos.use_cases.commands.list_commands_use_case import ListCommandsUseCase
from hefajstos.use_cases.commands.run_command_use_case import (
    CommandOutcome,
    RunCommandUseCase,
)


class ChatRepository:
    def __init__(
        self,
        start_agent_use_case: StartAgentUseCase,
        shutdown_agent_use_case: ShutdownAgentUseCase,
        stream_agent_responses_use_case: StreamAgentResponsesUseCase,
        send_message_use_case: SendMessageUseCase,
        answer_permission_use_case: AnswerPermissionUseCase,
        abort_turn_use_case: AbortTurnUseCase,
        list_commands_use_case: ListCommandsUseCase,
        run_command_use_case: RunCommandUseCase,
        change_model_use_case: ChangeModelUseCase,
    ) -> None:
        self.start_agent_use_case = start_agent_use_case
        self.shutdown_agent_use_case = shutdown_agent_use_case
        self.stream_agent_responses_use_case = stream_agent_responses_use_case
        self.send_message_use_case = send_message_use_case
        self.answer_permission_use_case = answer_permission_use_case
        self.abort_turn_use_case = abort_turn_use_case
        self.list_commands_use_case = list_commands_use_case
        self.run_command_use_case = run_command_use_case
        self.change_model_use_case = change_model_use_case

    async def start_agent(self) -> AgentInfoViewModel:
        return await self.start_agent_use_case()

    async def shutdown_agent(self) -> None:
        await self.shutdown_agent_use_case()

    def stream_agent_responses(self) -> AsyncGenerator[AgentStreamItem, None]:
        return self.stream_agent_responses_use_case()

    def send_message(self, prompt: str) -> None:
        self.send_message_use_case(prompt)

    def answer_permission(self, request_id: str, decision: PermissionDecision) -> bool:
        return self.answer_permission_use_case(request_id, decision)

    async def abort_turn(self) -> None:
        await self.abort_turn_use_case()

    def list_commands(self, prefix: str) -> list[CommandViewModel]:
        return self.list_commands_use_case(prefix)

    async def run_command(self, text: str) -> CommandOutcome:
        return await self.run_command_use_case(text)

    async def change_model(
        self, selection: ModelSelection
    ) -> ModelChangedViewModel | NoticeViewModel:
        return await self.change_model_use_case(selection)
