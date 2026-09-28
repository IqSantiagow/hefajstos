"""Drives the whole UI headlessly against the stub agent, through the real AgentService.

Not a unit test: it mounts the real app and walks one full turn, which is the
cheapest way to catch a broken stylesheet, a bad selector or a widget that is
updated before compose() has run. Widgets themselves stay untested on purpose.

    uv run python scripts/smoke_stub.py
"""

import asyncio
import os
import sys

os.environ["AGENT__ENGINE"] = "stub"

from hefajstos.containers.main_container import Container  # noqa: E402
from hefajstos.ui.app import HefajstosApp  # noqa: E402
from hefajstos.ui.screens.chat.modal_permission_screen import (  # noqa: E402
    ModalPermissionScreen,
)
from hefajstos.ui.screens.chat.widgets.widget_agent_message import (  # noqa: E402
    WidgetAgentMessage,
)
from hefajstos.ui.screens.chat.widgets.widget_chat_feed import (  # noqa: E402
    WidgetChatFeed,
)
from hefajstos.ui.screens.chat.widgets.widget_prompt_input import (  # noqa: E402
    PROMPT_INPUT_ID,
)
from hefajstos.ui.screens.chat.widgets.widget_status_header import (  # noqa: E402
    WidgetStatusHeader,
)
from hefajstos.ui.screens.chat.widgets.widget_tool_call import (  # noqa: E402
    WidgetToolCall,
)
from hefajstos.services.models.agent_events import AgentStatus  # noqa: E402
from textual.widgets import Input, Label, Static  # noqa: E402

WAIT_STEPS = 80
WAIT_STEP_SECONDS = 0.05


async def walk_one_turn(answer: str) -> bool:
    container = Container()
    container.wire(modules=["hefajstos.ui.app"])
    app = HefajstosApp()

    async with app.run_test(size=(100, 30)) as pilot:
        await pilot.pause()
        app.screen.query_one(f"#{PROMPT_INPUT_ID}", Input).value = "list the files"
        await pilot.press("enter")

        for _ in range(WAIT_STEPS):
            await pilot.pause(WAIT_STEP_SECONDS)
            if isinstance(app.screen, ModalPermissionScreen):
                break
        else:
            print("ERROR: the permission modal did not show up")
            return False

        print(
            f"  modal: {app.screen.view_model.title} -> {app.screen.view_model.summary}"
        )
        await pilot.press(answer)

        for _ in range(WAIT_STEPS):
            await pilot.pause(WAIT_STEP_SECONDS)

        feed = app.screen.query_one(WidgetChatFeed)
        for message in feed.query(WidgetAgentMessage):
            print("  AGENT:", message.query_one(".chat-entry-content", Static).content)
        for call in feed.query(WidgetToolCall):
            result = call.result.content if call.result else "—"
            call_line = f"{call.view_model.title} {call.view_model.summary}"
            print(f"  TOOL : {call_line} -> {result}")

        header = app.screen.query_one(WidgetStatusHeader)
        tokens = header.query_one("#status-tokens", Label).content
        print(f"  status: {header.agent_status.value} | tokens: {tokens}")
        return header.agent_status is AgentStatus.IDLE


async def main() -> int:
    for answer in ("y", "n"):
        print(f"--- turn answered with {answer!r} ---")
        if not await walk_one_turn(answer):
            return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
