from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentStatus(Enum):
    # The service never sends STARTING - the widgets show it until start() is done.
    STARTING = "starting"
    IDLE = "idle"
    THINKING = "thinking"


class PermissionDecision(Enum):
    APPROVE_ONCE = "approve_once"
    # The UI does not offer it yet, but the SDK supports it.
    APPROVE_FOR_SESSION = "approve_for_session"
    REJECT = "reject"
    USER_NOT_AVAILABLE = "user_not_available"


@dataclass
class AgentText:
    """A piece of the agent's answer.

    The chunks come first (is_final=False). Then the whole message arrives once
    more with is_final=True and replaces them.
    """

    message_id: str
    text: str
    is_final: bool


@dataclass
class ToolStarted:
    tool_call_id: str
    tool_name: str
    arguments: dict[str, Any]


@dataclass
class ToolFinished:
    tool_call_id: str
    success: bool
    content: str


@dataclass
class PermissionRequested:
    """The agent waits until request_id gets an answer."""

    request_id: str
    action: str
    summary: str
    detail: str
    requires_manual_approval: bool
    auto_approved: bool = False
    is_read_only: bool = False
    paths: list[str] = field(default_factory=list)


@dataclass
class TokensUsed:
    input_tokens: int
    output_tokens: int


@dataclass
class AgentError:
    message: str


@dataclass
class TurnFinished:
    """The agent is done with the prompt. Only the adapter sees it."""


AgentEvent = (
    AgentText
    | ToolStarted
    | ToolFinished
    | PermissionRequested
    | TokensUsed
    | AgentError
    | TurnFinished
)
