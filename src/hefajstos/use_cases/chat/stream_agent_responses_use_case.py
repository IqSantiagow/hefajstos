from collections.abc import AsyncGenerator

from hefajstos.presentation.view_models.chat_item_view_model import (
    ChatItem,
    build_chat_item,
)
from hefajstos.presentation.view_models.header_view_model import TokensViewModel
from hefajstos.presentation.view_models.permission_view_model import PermissionViewModel
from hefajstos.protocols.agent_protocol import AgentProtocol
from hefajstos.services.models.agent_events import (
    AgentStatus,
    PermissionRequested,
    TokensUsed,
)

AgentStreamItem = AgentStatus | TokensViewModel | PermissionViewModel | ChatItem


class StreamAgentResponsesUseCase:
    def __init__(self, agent_protocol: AgentProtocol) -> None:
        self.agent_protocol = agent_protocol

    async def __call__(self) -> AsyncGenerator[AgentStreamItem, None]:
        async for item in self.agent_protocol.consume_prompt_queue():
            if isinstance(item, AgentStatus):
                yield item
                continue

            if isinstance(item, TokensUsed):
                yield TokensViewModel.from_event(item)
                continue

            if isinstance(item, PermissionRequested) and not item.auto_approved:
                yield PermissionViewModel.from_event(item)
                continue

            chat_item = build_chat_item(item)

            if chat_item is not None:
                yield chat_item
