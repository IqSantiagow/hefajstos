import json
from dataclasses import dataclass
from typing import Any

from hefajstos.services.models.agent_events import (
    AgentError,
    AgentEvent,
    AgentText,
    PermissionRequested,
    ToolFinished,
    ToolStarted,
)


# Arguments shown on the tool line, most useful first. Anything else is shown
# as compact JSON.
_ARGUMENTS_SHOWN_ON_TOOL_LINE = (
    "command",
    "path",
    "file_path",
    "filePath",
    "pattern",
    "query",
    "url",
)


@dataclass(slots=True)
class UserMessageViewModel:
    content: str


@dataclass(slots=True)
class AgentTextViewModel:
    message_id: str
    text: str
    is_final: bool


@dataclass(slots=True)
class ToolCallViewModel:
    tool_call_id: str
    title: str
    summary: str


@dataclass(slots=True)
class ToolResultViewModel:
    tool_call_id: str
    content: str
    is_error: bool


@dataclass(slots=True)
class NoticeViewModel:
    content: str
    is_error: bool


@dataclass(slots=True)
class AutoApprovedViewModel:
    action: str
    summary: str


ChatItem = (
    UserMessageViewModel
    | AgentTextViewModel
    | ToolCallViewModel
    | ToolResultViewModel
    | NoticeViewModel
    | AutoApprovedViewModel
)


def build_chat_item(event: AgentEvent) -> ChatItem | None:
    """None for events the feed does not show."""
    if isinstance(event, AgentText):
        return AgentTextViewModel(
            message_id=event.message_id, text=event.text, is_final=event.is_final
        )

    if isinstance(event, ToolStarted):
        return ToolCallViewModel(
            tool_call_id=event.tool_call_id,
            title=event.tool_name,
            summary=summarize_tool_arguments(event.arguments),
        )

    if isinstance(event, ToolFinished):
        return ToolResultViewModel(
            tool_call_id=event.tool_call_id,
            content=event.content,
            is_error=not event.success,
        )

    if isinstance(event, PermissionRequested) and event.auto_approved:
        return AutoApprovedViewModel(action=event.action, summary=event.summary)

    if isinstance(event, AgentError):
        return NoticeViewModel(content=event.message, is_error=True)

    return None


def summarize_tool_arguments(arguments: dict[str, Any]) -> str:
    for key in _ARGUMENTS_SHOWN_ON_TOOL_LINE:
        value = arguments.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    if not arguments:
        return ""
    return json.dumps(arguments, ensure_ascii=False, separators=(",", ":"))
