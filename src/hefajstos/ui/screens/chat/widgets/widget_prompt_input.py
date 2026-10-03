from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalGroup
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Input, OptionList

from hefajstos.presentation.view_models.command_view_model import CommandViewModel
from hefajstos.services.models.agent_events import AgentStatus
from hefajstos.ui.screens.chat.widgets.widget_command_list import WidgetCommandList

READY_PLACEHOLDER = "What should I do? / for commands"
STARTING_PLACEHOLDER = "Starting the agent…"
LOCKED_PLACEHOLDER = "Answer in the panel above…"

PROMPT_INPUT_ID = "prompt-input"
COMMAND_LIST_ID = "command-list"

# These keys belong to the command list only while it is open. Otherwise
# check_action turns them off and the key goes on (tab moves the focus again).
COMMAND_LIST_ACTIONS = {
    "move_in_command_list",
    "complete_command",
    "close_command_list",
}


def is_command_prefix(value: str) -> bool:
    """'/mo' still picks a command; '/model x' already has its arguments."""
    return value.startswith("/") and " " not in value


class WidgetPromptInput(VerticalGroup):
    agent_status: reactive[AgentStatus] = reactive(AgentStatus.STARTING)

    # Input binds enter itself, so enter is handled in Input.Submitted instead.
    BINDINGS = [
        Binding("up", "move_in_command_list(-1)", show=False),
        Binding("down", "move_in_command_list(1)", show=False),
        Binding("tab", "complete_command", show=False),
        Binding("escape", "close_command_list", show=False),
    ]

    class UserPromptSubmitted(Message):
        def __init__(self, prompt: str) -> None:
            self.prompt = prompt
            super().__init__()

    class CommandSubmitted(Message):
        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    class CommandPrefixChanged(Message):
        """The screen answers with show_commands()."""

        def __init__(self, prefix: str) -> None:
            self.prefix = prefix
            super().__init__()

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.__is_locked = False

    def compose(self) -> ComposeResult:
        yield WidgetCommandList(id=COMMAND_LIST_ID, classes="hidden")
        yield Input(placeholder=STARTING_PLACEHOLDER, id=PROMPT_INPUT_ID, compact=True)

    @on(Input.Changed)
    def handle_input_changed(self, event: Input.Changed) -> None:
        if is_command_prefix(event.value):
            self.post_message(self.CommandPrefixChanged(event.value))
        else:
            self.command_list.hide()

    @on(Input.Submitted)
    def handle_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return

        # Enter on an open list runs the highlighted command, even for '/mo'.
        highlighted = self.command_list.highlighted_name
        if self.command_list.is_open and highlighted is not None:
            text = f"/{highlighted}"

        self.command_list.hide()
        self.prompt.value = ""
        if text.startswith("/"):
            self.post_message(self.CommandSubmitted(text))
        else:
            self.post_message(self.UserPromptSubmitted(event.value))

    @on(OptionList.OptionSelected, f"#{COMMAND_LIST_ID}")
    def handle_command_clicked(self, event: OptionList.OptionSelected) -> None:
        self.command_list.hide()
        self.prompt.value = ""
        self.post_message(self.CommandSubmitted(f"/{event.option.id}"))

    def show_commands(self, commands: list[CommandViewModel]) -> None:
        # The answer may come after the user has typed on - drop it then.
        if is_command_prefix(self.prompt.value):
            self.command_list.show_commands(commands)

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action in COMMAND_LIST_ACTIONS:
            return self.command_list.is_open
        return True

    def action_move_in_command_list(self, step: int) -> None:
        if step < 0:
            self.command_list.action_cursor_up()
        else:
            self.command_list.action_cursor_down()

    def action_complete_command(self) -> None:
        name = self.command_list.highlighted_name
        if name is None:
            return
        self.prompt.value = f"/{name} "
        self.prompt.cursor_position = len(self.prompt.value)

    def action_close_command_list(self) -> None:
        self.command_list.hide()

    def set_locked(self, is_locked: bool) -> None:
        """Locked while a panel above the prompt waits for an answer."""
        self.__is_locked = is_locked
        self.__update_prompt()

    def watch_agent_status(self, new_status: AgentStatus) -> None:
        self.__update_prompt()

    def focus_prompt(self) -> None:
        self.prompt.focus()

    @property
    def prompt(self) -> Input:
        return self.query_one(f"#{PROMPT_INPUT_ID}", Input)

    @property
    def command_list(self) -> WidgetCommandList:
        return self.query_one(f"#{COMMAND_LIST_ID}", WidgetCommandList)

    def __update_prompt(self) -> None:
        is_starting = self.agent_status == AgentStatus.STARTING
        self.prompt.disabled = is_starting or self.__is_locked
        if is_starting:
            self.prompt.placeholder = STARTING_PLACEHOLDER
        elif self.__is_locked:
            self.prompt.placeholder = LOCKED_PLACEHOLDER
        else:
            self.prompt.placeholder = READY_PLACEHOLDER
