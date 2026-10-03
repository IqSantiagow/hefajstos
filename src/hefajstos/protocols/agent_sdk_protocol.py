from collections.abc import AsyncGenerator
from typing import Protocol

from hefajstos.services.models.agent_events import AgentEvent, PermissionDecision
from hefajstos.services.models.model_choice import ModelChoice, ModelSelection


class AgentSdkProtocol(Protocol):
    model: str
    model_settings: dict[str, str]
    working_directory: str

    async def start(self) -> None: ...

    def send_and_stream(self, prompt: str) -> AsyncGenerator[AgentEvent, None]: ...

    def answer_permission(
        self, request_id: str, decision: PermissionDecision
    ) -> bool: ...

    async def list_models(self) -> list[ModelChoice]: ...

    async def set_model(self, selection: ModelSelection) -> None: ...

    async def abort(self) -> None: ...

    async def stop(self) -> None: ...
