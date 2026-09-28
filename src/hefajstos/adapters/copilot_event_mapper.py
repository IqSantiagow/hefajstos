import logging

from copilot import SessionEvent
from copilot.generated.session_events import (
    AssistantMessageData,
    AssistantMessageDeltaData,
    AssistantUsageData,
    PermissionRequest,
    PermissionRequestCustomTool,
    PermissionRequestExtensionEnvAccess,
    PermissionRequestExtensionManagement,
    PermissionRequestExtensionPermissionAccess,
    PermissionRequestFactory,
    PermissionRequestHook,
    PermissionRequestMcp,
    PermissionRequestMemory,
    PermissionRequestRead,
    PermissionRequestShell,
    PermissionRequestUrl,
    PermissionRequestWrite,
    SessionErrorData,
    SessionIdleData,
    ToolExecutionCompleteData,
    ToolExecutionStartData,
)

from hefajstos.services.models.agent_events import (
    AgentError,
    AgentEvent,
    AgentText,
    PermissionRequested,
    TokensUsed,
    ToolFinished,
    ToolStarted,
    TurnFinished,
)

logger = logging.getLogger(__name__)

# The feed shows a preview; the agent itself still gets the full text.
MAX_TOOL_RESULT_CHARACTERS = 2000

# A write request carries the whole diff. The modal has to stay readable.
MAX_PERMISSION_DETAIL_CHARACTERS = 1500


def map_session_event(event: SessionEvent) -> AgentEvent | None:
    """None for every event we do not use - the SDK has over a hundred of them.

    `permission.requested` is left out on purpose: the same request also comes
    through the on_permission_request callback and would show up twice.
    """
    data = event.data

    if isinstance(data, AssistantMessageDeltaData):
        return AgentText(
            message_id=data.message_id, text=data.delta_content, is_final=False
        )

    if isinstance(data, AssistantMessageData):
        return AgentText(message_id=data.message_id, text=data.content, is_final=True)

    if isinstance(data, ToolExecutionStartData):
        return ToolStarted(
            tool_call_id=data.tool_call_id,
            tool_name=data.tool_name,
            arguments=data.arguments if isinstance(data.arguments, dict) else {},
        )

    if isinstance(data, ToolExecutionCompleteData):
        return ToolFinished(
            tool_call_id=data.tool_call_id,
            success=data.success,
            content=_tool_result_text(data),
        )

    if isinstance(data, AssistantUsageData):
        return TokensUsed(
            input_tokens=data.input_tokens or 0,
            output_tokens=data.output_tokens or 0,
        )

    if isinstance(data, SessionErrorData):
        return AgentError(message=data.message)

    if isinstance(data, SessionIdleData):
        return TurnFinished()

    return None


def map_permission_request(
    request: PermissionRequest, request_id: str
) -> PermissionRequested:
    action, summary, detail = describe_permission_request(request)

    return PermissionRequested(
        request_id=request_id,
        action=action,
        summary=summary,
        detail=_shorten(detail, MAX_PERMISSION_DETAIL_CHARACTERS),
        requires_manual_approval=getattr(request, "managed_approval_required", False)
        is True,
    )


def describe_permission_request(request: PermissionRequest) -> tuple[str, str, str]:
    """(action, summary, detail). The action goes into the modal title."""
    if isinstance(request, PermissionRequestShell):
        return "run command", request.full_command_text, request.intention

    if isinstance(request, PermissionRequestWrite):
        return "write file", request.file_name, request.diff

    if isinstance(request, PermissionRequestRead):
        return "read file", request.path, request.intention

    if isinstance(request, PermissionRequestMcp):
        return (
            "MCP tool",
            f"{request.server_name}/{request.tool_name}",
            request.tool_title,
        )

    if isinstance(request, PermissionRequestUrl):
        return "open URL", request.url, request.intention

    if isinstance(request, PermissionRequestMemory):
        return "save to memory", request.fact, request.reason or ""

    if isinstance(request, PermissionRequestCustomTool):
        return "custom tool", request.tool_name, request.tool_description

    if isinstance(request, PermissionRequestHook):
        return "hook", request.tool_name, request.hook_message or ""

    if isinstance(request, PermissionRequestExtensionManagement):
        return (
            "manage extension",
            request.operation,
            request.extension_name or "",
        )

    if isinstance(request, PermissionRequestFactory):
        return "run agent factory", request.name, request.description

    if isinstance(request, PermissionRequestExtensionPermissionAccess):
        return (
            "extension permissions",
            request.extension_name,
            ", ".join(str(capability) for capability in request.capabilities),
        )

    if isinstance(request, PermissionRequestExtensionEnvAccess):
        return (
            "extension environment variables",
            request.extension_name,
            ", ".join(request.environment_variables),
        )

    logger.warning("Unknown permission request type %s", type(request).__name__)
    return "unknown action", type(request).__name__, ""


def _tool_result_text(data: ToolExecutionCompleteData) -> str:
    if data.error is not None:
        return data.error.message
    if data.result is not None:
        return _shorten(data.result.content, MAX_TOOL_RESULT_CHARACTERS)
    return ""


def _shorten(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n… ({len(text) - limit} more characters)"
