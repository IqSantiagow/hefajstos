from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup
from textual.css.query import NoMatches
from textual.events import Click
from textual.widgets import Label, Static

from hefajstos.presentation.view_models.chat_item_view_model import (
    ToolCallViewModel,
    ToolResultViewModel,
)
from hefajstos.ui.screens.chat.widgets.feed_ids import tool_widget_id

EMPTY_RESULT_TEXT = "(no output)"

TOOL_OUTPUT_PREVIEW_LINES = 10


def preview_tool_output(
    content: str, max_lines: int = TOOL_OUTPUT_PREVIEW_LINES
) -> str:
    lines = content.splitlines()
    hidden = len(lines) - max_lines
    if hidden <= 0:
        return content
    return "\n".join(lines[:max_lines]) + f"\n… {hidden} more lines (click to expand)"


class WidgetToolCall(VerticalGroup):
    DEFAULT_CLASSES = "chat-entry tool-entry"

    def __init__(self, view_model: ToolCallViewModel, **kwargs) -> None:
        super().__init__(id=tool_widget_id(view_model.tool_call_id), **kwargs)
        self.view_model = view_model
        self.result: ToolResultViewModel | None = None
        self.expanded = False

    def compose(self) -> ComposeResult:
        with HorizontalGroup(classes="tool-call-row"):
            yield Label(self.view_model.title, markup=False, classes="tool-name")
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
        self.set_class(not view_model.is_error, "-success")
        self.set_class(view_model.is_error, "-error")
        self.__show_result()

    def on_click(self, event: Click) -> None:
        if self.result is None:
            return
        self.expanded = not self.expanded
        self.__show_result()

    def __show_result(self) -> None:
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
        content = self.result.content or EMPTY_RESULT_TEXT
        return content if self.expanded else preview_tool_output(content)
