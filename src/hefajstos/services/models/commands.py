from dataclasses import dataclass
from enum import StrEnum

from hefajstos.services.models.model_choice import ModelChoice


class CommandSource(StrEnum):
    BUILT_IN = "built-in"
    PROVIDER = "provider"
    EXTENSION = "extension"


@dataclass
class CommandNotice:
    text: str
    is_error: bool


@dataclass
class ClearFeed:
    pass


@dataclass
class NewSessionStarted:
    pass


@dataclass
class OpenModelPicker:
    models: list[ModelChoice]
    current_model_id: str
    current_settings: dict[str, str]


CommandResult = CommandNotice | ClearFeed | NewSessionStarted | OpenModelPicker
