from textual.app import ComposeResult
from textual.containers import VerticalGroup
from textual.css.query import NoMatches
from textual.widgets import Label, Static

from hefajstos.ui.screens.chat.widgets.feed_ids import message_widget_id

AGENT_TITLE = "AGENT"
USER_TITLE = "YOU"


class WidgetAgentMessage(VerticalGroup):
    """Keeps its text in self.__text, because the first chunk often arrives
    before compose() has built the Static that shows it.

    markup=False everywhere: a diff or an `ls` output is full of [brackets].
    """

    DEFAULT_CLASSES = "chat-entry agent-entry"

    def __init__(self, message_id: str, **kwargs) -> None:
        super().__init__(id=message_widget_id(message_id), **kwargs)
        self.message_id = message_id
        self.__text = ""

    def compose(self) -> ComposeResult:
        yield Label(AGENT_TITLE, classes="chat-entry-title")
        yield Static(self.__text, markup=False, classes="chat-entry-content")

    def append_text(self, text: str) -> None:
        self.__text += text
        self.__show_text()

    def set_text(self, text: str) -> None:
        self.__text = text
        self.__show_text()

    def __show_text(self) -> None:
        try:
            self.query_one(".chat-entry-content", Static).update(self.__text)
        except NoMatches:
            # compose() has not run yet; it will show self.__text.
            pass


class WidgetUserMessage(VerticalGroup):
    DEFAULT_CLASSES = "chat-entry user-entry"

    def __init__(self, content: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.content = content

    def compose(self) -> ComposeResult:
        yield Label(USER_TITLE, classes="chat-entry-title")
        yield Static(self.content, markup=False, classes="chat-entry-content")
