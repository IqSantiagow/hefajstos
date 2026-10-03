from collections.abc import AsyncGenerator
from typing import Protocol

from hefajstos.services.models.agent_events import (
    AgentEvent,
    AgentStatus,
    PermissionDecision,
)
from hefajstos.services.models.model_choice import ModelChoice, ModelSelection


class AgentProtocol(Protocol):
    model: str
    model_settings: dict[str, str]
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

    async def list_models(self) -> list[ModelChoice]: ...

    async def set_model(self, selection: ModelSelection) -> None: ...
