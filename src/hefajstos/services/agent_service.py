import asyncio
import logging
from collections.abc import AsyncGenerator
from dataclasses import replace

from hefajstos.protocols.agent_sdk_protocol import AgentSdkProtocol
from hefajstos.services.models.agent_events import (
    AgentError,
    AgentEvent,
    AgentStatus,
    PermissionDecision,
    PermissionRequested,
    TokensUsed,
)

logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self, agent_sdk: AgentSdkProtocol, auto_approve_tools: bool) -> None:
        self.agent_sdk = agent_sdk
        self.model = agent_sdk.model
        self.working_directory = agent_sdk.working_directory
        self.__auto_approve_tools = auto_approve_tools
        self.__prompt_queue: asyncio.Queue[str] = asyncio.Queue()
        self.__input_tokens = 0
        self.__output_tokens = 0

    async def start(self) -> None:
        await self.agent_sdk.start()

    async def shutdown(self) -> None:
        await self.agent_sdk.stop()

    def add_prompt_to_queue(self, prompt: str) -> None:
        self.__prompt_queue.put_nowait(prompt)

    def answer_permission(self, request_id: str, decision: PermissionDecision) -> bool:
        return self.agent_sdk.answer_permission(request_id, decision)

    async def abort_turn(self) -> None:
        await self.agent_sdk.abort()

    async def consume_prompt_queue(
        self,
    ) -> AsyncGenerator[AgentStatus | AgentEvent, None]:
        while True:
            prompt = await self.__prompt_queue.get()

            yield AgentStatus.THINKING

            try:
                async for event in self.agent_sdk.send_and_stream(prompt):
                    if isinstance(event, PermissionRequested):
                        event = self.__auto_approve_if_allowed(event)
                    if isinstance(event, TokensUsed):
                        event = self.__add_to_session_tokens(event)
                    yield event
            except Exception as error:
                logger.exception("Agent turn failed", exc_info=error)
                yield AgentError(message=f"The agent turn failed: {error}")

            yield AgentStatus.IDLE

    def __auto_approve_if_allowed(
        self, request: PermissionRequested
    ) -> PermissionRequested:
        if not self.__auto_approve_tools or request.requires_manual_approval:
            return request

        self.agent_sdk.answer_permission(
            request.request_id, PermissionDecision.APPROVE_ONCE
        )
        # Still goes to the feed, so the user sees what was approved for them.
        return replace(request, auto_approved=True)

    def __add_to_session_tokens(self, tokens: TokensUsed) -> TokensUsed:
        self.__input_tokens += tokens.input_tokens
        self.__output_tokens += tokens.output_tokens
        return TokensUsed(
            input_tokens=self.__input_tokens, output_tokens=self.__output_tokens
        )
