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
    APPROVE_FOR_SESSION = "approve_for_session"
    REJECT = "reject"
    USER_NOT_AVAILABLE = "user_not_available"


@dataclass
class AgentText:
    # The final message replaces the chunks that came before it.
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
    pass


AgentEvent = (
    AgentText
    | ToolStarted
    | ToolFinished
    | PermissionRequested
    | TokensUsed
    | AgentError
    | TurnFinished
)
