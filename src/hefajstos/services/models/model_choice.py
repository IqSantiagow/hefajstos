"""What a provider offers in /model, as plain data.

Every provider has other knobs (Copilot: reasoning effort and a long context
tier). The adapter describes them as ModelSettings and the UI draws whatever it
gets, so a new provider brings new data, not a new picker.
"""

from dataclasses import dataclass

# The first choice of every setting: send nothing and let the provider decide.
PROVIDER_DEFAULT = "default"


@dataclass
class ModelSetting:
    key: str
    label: str
    choices: list[str]


@dataclass
class ModelChoice:
    id: str
    name: str
    context_window_tokens: int | None
    settings: list[ModelSetting]


@dataclass
class ModelSelection:
    model_id: str
    # setting key -> one of its choices
    settings: dict[str, str]
