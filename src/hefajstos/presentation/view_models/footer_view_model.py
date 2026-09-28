from dataclasses import dataclass

from hefajstos.services.models.agent_events import TokensUsed


@dataclass(slots=True)
class AgentInfoViewModel:
    model: str
    working_directory: str


@dataclass(slots=True)
class TokensViewModel:
    input_tokens: int
    output_tokens: int

    @classmethod
    def from_event(cls, tokens: TokensUsed) -> "TokensViewModel":
        return cls(input_tokens=tokens.input_tokens, output_tokens=tokens.output_tokens)
