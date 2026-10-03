from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.css.query import NoMatches
from textual.widgets import Static

from hefajstos.presentation.view_models.chat_item_view_model import (
    AgentTextViewModel,
    AutoApprovedViewModel,
    NoticeViewModel,
    ToolCallViewModel,
    ToolResultViewModel,
    UserMessageViewModel,
)
from hefajstos.ui.screens.chat.widgets.feed_ids import message_widget_id, tool_widget_id
from hefajstos.ui.screens.chat.widgets.widget_agent_message import (
    WidgetAgentMessage,
    WidgetUserMessage,
)
from hefajstos.ui.screens.chat.widgets.widget_forge_logo import WidgetForgeLogo
from hefajstos.ui.screens.chat.widgets.widget_tool_call import WidgetToolCall

NOTICE_ENTRY = "notice-entry"
ERROR_ENTRY = "error-entry"

MAX_ENTRIES = 300

WELCOME_TEXT = "ctrl+x abort · ctrl+c quit · click a tool result to expand"


class WidgetChatFeed(VerticalScroll):
    def on_mount(self) -> None:
        self.anchor()

    def compose(self) -> ComposeResult:
        yield WidgetForgeLogo()
        yield Static(WELCOME_TEXT, markup=False, classes=f"chat-entry {NOTICE_ENTRY}")

    def add_user_message(self, user_message: UserMessageViewModel) -> None:
        self.__add_entry(WidgetUserMessage(user_message.content))

    def show_agent_text(self, agent_text: AgentTextViewModel) -> None:
        try:
            message = self.query_one(
                f"#{message_widget_id(agent_text.message_id)}", WidgetAgentMessage
            )
        except NoMatches:
            message = WidgetAgentMessage(agent_text.message_id)
            self.__add_entry(message)

        if agent_text.is_final:
            message.set_text(agent_text.text)
        else:
            message.append_text(agent_text.text)

    def add_tool_call(self, tool_call: ToolCallViewModel) -> None:
        self.__add_entry(WidgetToolCall(tool_call))

    def show_tool_result(self, tool_result: ToolResultViewModel) -> None:
        try:
            tool_call = self.query_one(
                f"#{tool_widget_id(tool_result.tool_call_id)}", WidgetToolCall
            )
        except NoMatches:
            # The call was already removed from the top, so show the result alone.
            self.add_notice(
                NoticeViewModel(
                    content=tool_result.content,
                    is_error=tool_result.is_error,
                )
            )
            return

        tool_call.set_result(tool_result)

    def add_auto_approved(self, auto_approved: AutoApprovedViewModel) -> None:
        self.add_notice(
            NoticeViewModel(
                content=f"Auto-approved: {auto_approved.action}"
                f" — {auto_approved.summary}",
                is_error=False,
            )
        )

    def add_notice(self, notice: NoticeViewModel) -> None:
        entry_class = ERROR_ENTRY if notice.is_error else NOTICE_ENTRY
        self.__add_entry(
            Static(notice.content, markup=False, classes=f"chat-entry {entry_class}")
        )

    def clear(self) -> None:
        self.remove_children()

    def __add_entry(self, widget) -> None:
        self.mount(widget)

        too_many = len(self.children) - MAX_ENTRIES
        if too_many > 0:
            for oldest in list(self.children)[:too_many]:
                oldest.remove()
