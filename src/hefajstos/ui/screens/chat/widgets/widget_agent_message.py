from textual.widgets import Static

from hefajstos.ui.screens.chat.widgets.feed_ids import message_widget_id


class WidgetAgentMessage(Static):
    """Keeps its text in self.__text, because chunks are appended one by one
    and Static only knows how to replace its content. The blank lines around
    the text are not shown - the margin between entries does that job.

    markup=False everywhere: a diff or an `ls` output is full of [brackets].
    """

    DEFAULT_CLASSES = "chat-entry agent-entry"

    def __init__(self, message_id: str, **kwargs) -> None:
        super().__init__("", markup=False, id=message_widget_id(message_id), **kwargs)
        self.message_id = message_id
        self.__text = ""

    def append_text(self, text: str) -> None:
        self.__text += text
        self.update(self.__text.strip())

    def set_text(self, text: str) -> None:
        self.__text = text
        self.update(self.__text.strip())


class WidgetUserMessage(Static):
    DEFAULT_CLASSES = "chat-entry user-entry"

    def __init__(self, content: str, **kwargs) -> None:
        super().__init__(content, markup=False, **kwargs)
