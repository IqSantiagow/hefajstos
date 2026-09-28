from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup
from textual.css.query import NoMatches
from textual.widgets import Label, Static

from hefajstos.presentation.view_models.chat_item_view_model import (
    ToolCallViewModel,
    ToolResultViewModel,
)
from hefajstos.ui.screens.chat.widgets.feed_ids import tool_widget_id

EMPTY_RESULT_TEXT = "(no output)"


class WidgetToolCall(VerticalGroup):
    """Keeps the result in self.result - a fast tool can finish before compose()."""

    DEFAULT_CLASSES = "chat-entry tool-entry"

    def __init__(self, view_model: ToolCallViewModel, **kwargs) -> None:
        super().__init__(id=tool_widget_id(view_model.tool_call_id), **kwargs)
        self.view_model = view_model
        self.result: ToolResultViewModel | None = None

    def compose(self) -> ComposeResult:
        with HorizontalGroup(classes="tool-call-row"):
            yield Label(self.view_model.title, classes="chat-entry-title")
            yield Static(
                self.view_model.summary, markup=False, classes="tool-call-summary"
            )
        yield Static(
            self.__result_text(),
            markup=False,
            classes="tool-result" if self.result else "tool-result hidden",
        )

    def set_result(self, view_model: ToolResultViewModel) -> None:
        self.result = view_model
        self.set_class(view_model.is_error, "-error")
        try:
            result = self.query_one(".tool-result", Static)
        except NoMatches:
            # compose() has not run yet; it will render the stored result.
            return
        result.update(self.__result_text())
        result.remove_class("hidden")

    def __result_text(self) -> str:
        if self.result is None:
            return ""
        return self.result.content or EMPTY_RESULT_TEXT
