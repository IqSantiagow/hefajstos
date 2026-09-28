from collections.abc import AsyncGenerator
from typing import Protocol

from hefajstos.services.models.agent_events import (
    AgentEvent,
    AgentStatus,
    PermissionDecision,
)


class AgentProtocol(Protocol):
    model: str
    working_directory: str

    async def start(self) -> None: ...

    async def shutdown(self) -> None: ...

    def add_prompt_to_queue(self, prompt: str) -> None: ...

    def consume_prompt_queue(
        self,
    ) -> AsyncGenerator[AgentStatus | AgentEvent, None]: ...

    def answer_permission(
        self, request_id: str, decision: PermissionDecision
    ) -> bool: ...

    async def abort_turn(self) -> None: ...
