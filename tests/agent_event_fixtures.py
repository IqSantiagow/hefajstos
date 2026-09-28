from datetime import datetime, timezone
from uuid import UUID

from copilot import SessionEvent, SessionEventType
from copilot.generated.session_events import (
    AssistantMessageData,
    AssistantMessageDeltaData,
    AssistantUsageData,
    SessionErrorData,
    SessionIdleData,
    ToolExecutionCompleteData,
    ToolExecutionCompleteError,
    ToolExecutionCompleteResult,
    ToolExecutionStartData,
)

FIXED_EVENT_ID = UUID("00000000-0000-4000-8000-000000000000")
FIXED_TIMESTAMP = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_session_event(data, event_type: SessionEventType) -> SessionEvent:
    return SessionEvent(
        data=data,
        id=FIXED_EVENT_ID,
        timestamp=FIXED_TIMESTAMP,
        type=event_type,
    )


def make_text_delta(**overrides) -> SessionEvent:
    defaults = dict(delta_content="Hel", message_id="msg-1")
    defaults.update(overrides)
    return make_session_event(
        AssistantMessageDeltaData(**defaults), SessionEventType.ASSISTANT_MESSAGE_DELTA
    )


def make_text_done(**overrides) -> SessionEvent:
    defaults = dict(content="Hello", message_id="msg-1")
    defaults.update(overrides)
    return make_session_event(
        AssistantMessageData(**defaults), SessionEventType.ASSISTANT_MESSAGE
    )


def make_tool_start(**overrides) -> SessionEvent:
    defaults = dict(
        tool_call_id="call-1", tool_name="execute", arguments={"command": "ls"}
    )
    defaults.update(overrides)
    return make_session_event(
        ToolExecutionStartData(**defaults), SessionEventType.TOOL_EXECUTION_START
    )


def make_tool_complete(**overrides) -> SessionEvent:
    defaults = dict(
        success=True,
        tool_call_id="call-1",
        result=ToolExecutionCompleteResult(content="README.md"),
    )
    defaults.update(overrides)
    return make_session_event(
        ToolExecutionCompleteData(**defaults), SessionEventType.TOOL_EXECUTION_COMPLETE
    )


def make_tool_failure(message: str = "command not found") -> SessionEvent:
    return make_tool_complete(
        success=False,
        result=None,
        error=ToolExecutionCompleteError(message=message),
    )


def make_session_idle(**overrides) -> SessionEvent:
    defaults = dict(aborted=False)
    defaults.update(overrides)
    return make_session_event(
        SessionIdleData(**defaults), SessionEventType.SESSION_IDLE
    )


def make_usage(**overrides) -> SessionEvent:
    defaults = dict(model="gpt-5", input_tokens=100, output_tokens=20)
    defaults.update(overrides)
    return make_session_event(
        AssistantUsageData(**defaults), SessionEventType.ASSISTANT_USAGE
    )


def make_session_error(**overrides) -> SessionEvent:
    defaults = dict(error_type="rate_limit", message="Too many requests")
    defaults.update(overrides)
    return make_session_event(
        SessionErrorData(**defaults), SessionEventType.SESSION_ERROR
    )
