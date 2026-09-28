"""SDK ids can contain characters a Textual id may not, so both mounting and
looking up a widget go through these functions."""

import re

MESSAGE_ID_PREFIX = "message-"
TOOL_ID_PREFIX = "tool-"

_ILLEGAL_IN_A_SELECTOR = re.compile(r"[^a-zA-Z0-9_-]")


def sanitize_id(raw_id: str) -> str:
    """Replace everything a Textual selector cannot contain."""
    cleaned = _ILLEGAL_IN_A_SELECTOR.sub("-", raw_id)
    return cleaned or "unknown"


def message_widget_id(message_id: str) -> str:
    return MESSAGE_ID_PREFIX + sanitize_id(message_id)


def tool_widget_id(tool_call_id: str) -> str:
    return TOOL_ID_PREFIX + sanitize_id(tool_call_id)
