from textual.app import ComposeResult
from textual.containers import HorizontalGroup
from textual.reactive import reactive
from textual.widgets import Label

from hefajstos.presentation.view_models.header_view_model import (
    STATUS_LABELS,
    AgentInfoViewModel,
    TokensViewModel,
)
from hefajstos.services.models.agent_events import AgentStatus

BRAND = "HEFAJSTOS"


class WidgetStatusHeader(HorizontalGroup):
    DEFAULT_CLASSES = "status-header"

    agent_status: reactive[AgentStatus] = reactive(AgentStatus.STARTING)

    def compose(self) -> ComposeResult:
        yield Label(BRAND, classes="status-brand")
        yield Label("—", id="status-model", classes="status-value")
        yield Label("—", id="status-directory", classes="status-directory")
        yield Label("↑ 0 / ↓ 0", id="status-tokens", classes="status-value")
        yield Label("", id="status-state")

    def show_agent_info(self, agent_info: AgentInfoViewModel) -> None:
        self.query_one("#status-model", Label).update(agent_info.model_text)
        self.query_one("#status-directory", Label).update(agent_info.directory_text)

    def show_tokens(self, tokens: TokensViewModel) -> None:
        self.query_one("#status-tokens", Label).update(tokens.text)

    def watch_agent_status(self, new_status: AgentStatus) -> None:
        status = self.query_one("#status-state", Label)
        status.update(STATUS_LABELS[new_status])
        # set_classes replaces all classes, so the previous status class goes away.
        status.set_classes(f"status-state -{new_status.value}")
