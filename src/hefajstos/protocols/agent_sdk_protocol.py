from collections.abc import AsyncGenerator
from typing import Protocol

from hefajstos.services.models.agent_events import AgentEvent, PermissionDecision


class AgentSdkProtocol(Protocol):
    model: str
    working_directory: str

    async def start(self) -> None: ...

    def send_and_stream(self, prompt: str) -> AsyncGenerator[AgentEvent, None]:
        """Send the prompt and yield what the agent does until it is finished."""
        ...

    def answer_permission(self, request_id: str, decision: PermissionDecision) -> bool:
        """False means the request is gone - it timed out or was aborted."""
        ...

    async def abort(self) -> None: ...

    async def stop(self) -> None: ...
