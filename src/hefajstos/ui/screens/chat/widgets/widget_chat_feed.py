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
from hefajstos.ui.screens.chat.widgets.widget_tool_call import WidgetToolCall

# CSS classes of plain feed entries - they have to match ui/css.tcss.
NOTICE_ENTRY = "notice-entry"
ERROR_ENTRY = "error-entry"

# Keeps the DOM small. Older entries are removed from the top.
MAX_ENTRIES = 300

WELCOME_TEXT = "hefajstos  ctrl+x abort · ctrl+c quit · click a tool result to expand"


class WidgetChatFeed(VerticalScroll):
    def compose(self) -> ComposeResult:
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
        self.__scroll_down_if_at_bottom()

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
        self.__scroll_down_if_at_bottom()

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

    def __add_entry(self, widget) -> None:
        was_at_bottom = self.__is_at_bottom()
        self.mount(widget)

        too_many = len(self.children) - MAX_ENTRIES
        if too_many > 0:
            for oldest in list(self.children)[:too_many]:
                oldest.remove()

        if was_at_bottom:
            self.call_after_refresh(self.scroll_end, animate=False)

    def __scroll_down_if_at_bottom(self) -> None:
        if self.__is_at_bottom():
            self.call_after_refresh(self.scroll_end, animate=False)

    def __is_at_bottom(self) -> bool:
        # Only follow new text when the user has not scrolled up to read history.
        return self.scroll_offset.y >= self.max_scroll_y - 1
