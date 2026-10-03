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
    settings: dict[str, str]
