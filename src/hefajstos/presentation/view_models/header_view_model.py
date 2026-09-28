from dataclasses import dataclass
from pathlib import Path

from hefajstos.services.models.agent_events import AgentStatus, TokensUsed

STATUS_LABELS = {
    AgentStatus.STARTING: "starting",
    AgentStatus.IDLE: "ready",
    AgentStatus.THINKING: "thinking",
}


@dataclass(slots=True)
class AgentInfoViewModel:
    model_text: str
    directory_text: str

    @classmethod
    def from_agent(cls, model: str, working_directory: str) -> "AgentInfoViewModel":
        return cls(model_text=model, directory_text=shorten_home(working_directory))


@dataclass(slots=True)
class TokensViewModel:
    text: str

    @classmethod
    def from_event(cls, tokens: TokensUsed) -> "TokensViewModel":
        return cls(
            text=f"↑ {format_thousands(tokens.input_tokens)}"
            f" / ↓ {format_thousands(tokens.output_tokens)}"
        )


def shorten_home(directory: str) -> str:
    """'/Users/me/Projects/foo' -> '~/Projects/foo'."""
    home = str(Path.home())
    if directory == home:
        return "~"
    if directory.startswith(home + "/"):
        return "~" + directory[len(home) :]
    return directory


def format_thousands(value: int) -> str:
    """1284 -> '1 284'"""
    return f"{value:,}".replace(",", " ")
