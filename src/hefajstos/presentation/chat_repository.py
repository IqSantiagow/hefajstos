from collections.abc import AsyncGenerator

from hefajstos.presentation.view_models.header_view_model import AgentInfoViewModel
from hefajstos.services.models.agent_events import PermissionDecision
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


class ChatRepository:
    def __init__(
        self,
        start_agent_use_case: StartAgentUseCase,
        shutdown_agent_use_case: ShutdownAgentUseCase,
        stream_agent_responses_use_case: StreamAgentResponsesUseCase,
        send_message_use_case: SendMessageUseCase,
        answer_permission_use_case: AnswerPermissionUseCase,
        abort_turn_use_case: AbortTurnUseCase,
    ) -> None:
        self.start_agent_use_case = start_agent_use_case
        self.shutdown_agent_use_case = shutdown_agent_use_case
        self.stream_agent_responses_use_case = stream_agent_responses_use_case
        self.send_message_use_case = send_message_use_case
        self.answer_permission_use_case = answer_permission_use_case
        self.abort_turn_use_case = abort_turn_use_case

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
