import logging

from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer

from hefajstos.presentation.chat_repository import ChatRepository
from hefajstos.presentation.view_models.chat_item_view_model import (
    AgentTextViewModel,
    NoticeViewModel,
    ToolCallViewModel,
    ToolResultViewModel,
    UserMessageViewModel,
)
from hefajstos.presentation.view_models.header_view_model import TokensViewModel
from hefajstos.presentation.view_models.permission_view_model import PermissionViewModel
from hefajstos.services.models.agent_events import AgentStatus, PermissionDecision
from hefajstos.ui.screens.chat.modal_permission_screen import ModalPermissionScreen
from hefajstos.ui.screens.chat.widgets.widget_chat_feed import WidgetChatFeed
from hefajstos.ui.screens.chat.widgets.widget_prompt_input import WidgetPromptInput
from hefajstos.ui.screens.chat.widgets.widget_status_header import WidgetStatusHeader

logger = logging.getLogger(__name__)

EXPIRED_PERMISSION_MESSAGE = (
    "The permission request expired or the turn was aborted - the answer was not used."
)

DECISION_LABELS = {
    PermissionDecision.APPROVE_ONCE: "approved",
    PermissionDecision.APPROVE_FOR_SESSION: "approved for the session",
    PermissionDecision.REJECT: "rejected",
    PermissionDecision.USER_NOT_AVAILABLE: "no answer",
}


class ChatScreen(Screen):
    BINDINGS = [
        # priority, or the focused Input takes ctrl+x as "cut" and the turn goes on.
        Binding("ctrl+x", "abort_turn", "Abort turn", priority=True),
    ]

    def __init__(self, chat_repository: ChatRepository, **kwargs) -> None:
        super().__init__(**kwargs)
        self.chat_repository = chat_repository

    def compose(self) -> ComposeResult:
        yield WidgetStatusHeader(id="status-header")
        yield WidgetChatFeed(id="chat-feed")
        yield WidgetPromptInput(id="prompt-row")
        yield Footer()

    def on_mount(self) -> None:
        self.set_up_agent_stream_worker()
        self.start_agent_worker()

    @work
    async def start_agent_worker(self) -> None:
        """The first run also downloads the Copilot runtime, so it can take a while."""
        try:
            agent_info = await self.chat_repository.start_agent()
        except Exception as e:
            logger.exception("Failed to start the agent", exc_info=e)
            self.notify(f"Could not start the agent: {e}", severity="error")
            self.feed.add_notice(NoticeViewModel(content=str(e), is_error=True))
            return

        self.header.show_agent_info(agent_info)
        self.header.agent_status = AgentStatus.IDLE
        self.prompt_input.agent_status = AgentStatus.IDLE
        self.prompt_input.focus_prompt()

    @work
    async def set_up_agent_stream_worker(self) -> None:
        """The only consumer of the agent stream.

        A permission request parks this worker on the modal. That is fine: the
        agent waits for the answer anyway, so nothing new can arrive meanwhile.
        """
        async for item in self.chat_repository.stream_agent_responses():
            if isinstance(item, AgentStatus):
                self.header.agent_status = item
                self.prompt_input.agent_status = item
            elif isinstance(item, TokensViewModel):
                self.header.show_tokens(item)
            elif isinstance(item, PermissionViewModel):
                await self.ask_for_permission(item)
            elif isinstance(item, AgentTextViewModel):
                self.feed.show_agent_text(item)
            elif isinstance(item, ToolCallViewModel):
                self.feed.add_tool_call(item)
            elif isinstance(item, ToolResultViewModel):
                self.feed.show_tool_result(item)
            elif isinstance(item, NoticeViewModel):
                self.feed.add_notice(item)

    async def ask_for_permission(self, permission: PermissionViewModel) -> None:
        decision = await self.app.push_screen_wait(ModalPermissionScreen(permission))
        self.feed.add_notice(
            NoticeViewModel(
                content=f"{permission.title}: {DECISION_LABELS[decision]}"
                f" — {permission.summary}",
                is_error=False,
            )
        )
        if not self.chat_repository.answer_permission(permission.request_id, decision):
            self.notify(EXPIRED_PERMISSION_MESSAGE, severity="warning")

    @on(WidgetPromptInput.UserPromptSubmitted)
    def handle_user_prompt_submitted(
        self, message: WidgetPromptInput.UserPromptSubmitted
    ) -> None:
        # Echo first, then send - so the answer can never land above the question.
        self.feed.add_user_message(UserMessageViewModel(content=message.prompt))
        self.chat_repository.send_message(message.prompt)

    async def action_abort_turn(self) -> None:
        await self.chat_repository.abort_turn()

    @property
    def feed(self) -> WidgetChatFeed:
        return self.query_one("#chat-feed", WidgetChatFeed)

    @property
    def header(self) -> WidgetStatusHeader:
        return self.query_one("#status-header", WidgetStatusHeader)

    @property
    def prompt_input(self) -> WidgetPromptInput:
        return self.query_one("#prompt-row", WidgetPromptInput)
