from pathlib import Path

from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup
from textual.widgets import Label

from hefajstos.presentation.view_models.footer_view_model import (
    AgentInfoViewModel,
    TokensViewModel,
)


def shorten_home(directory: str) -> str:
    home = str(Path.home())
    if directory == home:
        return "~"
    if directory.startswith(home + "/"):
        return "~" + directory[len(home) :]
    return directory


def format_token_count(count: int) -> str:
    if count < 1_000:
        return str(count)
    if count < 10_000:
        return f"{count / 1_000:.1f}k"
    if count < 1_000_000:
        return f"{round(count / 1_000)}k"
    if count < 10_000_000:
        return f"{count / 1_000_000:.1f}M"
    return f"{round(count / 1_000_000)}M"


class WidgetStatusFooter(VerticalGroup):
    DEFAULT_CLASSES = "status-footer"

    def compose(self) -> ComposeResult:
        yield Label("", id="footer-directory", markup=False)
        with HorizontalGroup(classes="footer-stats"):
            yield Label("", id="footer-tokens", markup=False)
            yield Label("", id="footer-model", markup=False)

    def show_agent_info(self, agent_info: AgentInfoViewModel) -> None:
        self.query_one("#footer-model", Label).update(
            " · ".join([agent_info.model, *agent_info.model_settings])
        )
        self.query_one("#footer-directory", Label).update(
            shorten_home(agent_info.working_directory)
        )

    def show_tokens(self, tokens: TokensViewModel) -> None:
        self.query_one("#footer-tokens", Label).update(
            f"↑{format_token_count(tokens.input_tokens)}"
            f" ↓{format_token_count(tokens.output_tokens)}"
        )
