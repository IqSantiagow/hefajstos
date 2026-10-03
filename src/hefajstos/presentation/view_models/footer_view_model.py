from dataclasses import dataclass, field

from hefajstos.services.models.agent_events import TokensUsed
from hefajstos.services.models.model_choice import PROVIDER_DEFAULT


@dataclass(slots=True)
class AgentInfoViewModel:
    model: str
    working_directory: str
    # Only what differs from the provider's default, e.g. ["high"].
    model_settings: list[str] = field(default_factory=list)


def describe_model_settings(settings: dict[str, str]) -> list[str]:
    return [value for value in settings.values() if value != PROVIDER_DEFAULT]


@dataclass(slots=True)
class TokensViewModel:
    input_tokens: int
    output_tokens: int

    @classmethod
    def from_event(cls, tokens: TokensUsed) -> "TokensViewModel":
        return cls(input_tokens=tokens.input_tokens, output_tokens=tokens.output_tokens)
