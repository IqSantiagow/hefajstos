"""A slash command returns data. ChatScreen decides what to draw for it."""

from dataclasses import dataclass
from enum import StrEnum

from hefajstos.services.models.model_choice import ModelChoice


class CommandSource(StrEnum):
    BUILT_IN = "built-in"
    # Commands only one provider has. None exist yet.
    PROVIDER = "provider"
    EXTENSION = "extension"


@dataclass
class CommandNotice:
    text: str
    is_error: bool


@dataclass
class ClearFeed:
    """Only the feed is cleared - the agent keeps its history."""


@dataclass
class OpenModelPicker:
    models: list[ModelChoice]
    current_model_id: str
    current_settings: dict[str, str]


CommandResult = CommandNotice | ClearFeed | OpenModelPicker
