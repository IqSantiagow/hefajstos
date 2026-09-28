from textual import on
from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Input, Label

from hefajstos.services.models.agent_events import AgentStatus

PROMPT_MARKER = "›"
READY_PLACEHOLDER = "What should I do?"
STARTING_PLACEHOLDER = "Starting the agent…"
BUSY_TEXT = "working…"

PROMPT_INPUT_ID = "prompt-input"


class WidgetPromptInput(VerticalGroup):
    agent_status: reactive[AgentStatus] = reactive(AgentStatus.STARTING)

    class UserPromptSubmitted(Message):
        def __init__(self, prompt: str) -> None:
            self.prompt = prompt
            super().__init__()

    def compose(self) -> ComposeResult:
        with HorizontalGroup(classes="prompt-row"):
            yield Label(PROMPT_MARKER, classes="prompt-marker")
            yield Input(
                placeholder=STARTING_PLACEHOLDER, id=PROMPT_INPUT_ID, compact=True
            )
            yield Label(BUSY_TEXT, id="prompt-busy", classes="prompt-busy hidden")

    @on(Input.Submitted)
    def handle_input_submitted(self, event: Input.Submitted) -> None:
        if not event.value.strip():
            return
        self.post_message(self.UserPromptSubmitted(event.value))
        self.query_one(f"#{PROMPT_INPUT_ID}", Input).value = ""

    def watch_agent_status(self, new_status: AgentStatus) -> None:
        is_starting = new_status == AgentStatus.STARTING

        prompt = self.query_one(f"#{PROMPT_INPUT_ID}", Input)
        prompt.disabled = is_starting
        prompt.placeholder = STARTING_PLACEHOLDER if is_starting else READY_PLACEHOLDER

        busy = self.query_one("#prompt-busy", Label)
        busy.set_class(new_status == AgentStatus.IDLE, "hidden")

    def focus_prompt(self) -> None:
        self.query_one(f"#{PROMPT_INPUT_ID}", Input).focus()
