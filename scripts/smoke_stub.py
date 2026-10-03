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
from hefajstos.ui.screens.chat.widgets.widget_command_list import (  # noqa: E402
    WidgetCommandList,
)
from hefajstos.ui.screens.chat.widgets.widget_model_picker import (  # noqa: E402
    WidgetModelPicker,
)
from hefajstos.ui.screens.chat.widgets.widget_forge_logo import (  # noqa: E402
    READY_TEXT,
    WidgetForgeLogo,
)
from hefajstos.ui.screens.chat.widgets.widget_prompt_input import (  # noqa: E402
    PROMPT_INPUT_ID,
)
from hefajstos.ui.screens.chat.widgets.widget_status_footer import (  # noqa: E402
    WidgetStatusFooter,
)
from hefajstos.ui.screens.chat.widgets.widget_tool_call import (  # noqa: E402
    WidgetToolCall,
)
from hefajstos.ui.screens.chat.widgets.widget_working_indicator import (  # noqa: E402
    WidgetWorkingIndicator,
)
from hefajstos.services.models.agent_events import AgentStatus  # noqa: E402
from textual.widgets import Input, Label  # noqa: E402

WAIT_STEPS = 80
WAIT_STEP_SECONDS = 0.05


async def walk_one_turn(answer: str) -> bool:
    container = Container()
    container.wire(modules=["hefajstos.ui.app"])
    app = HefajstosApp()

    async with app.run_test(size=(100, 30)) as pilot:
        indicator = app.screen.query_one(WidgetWorkingIndicator)
        for _ in range(WAIT_STEPS):
            await pilot.pause(WAIT_STEP_SECONDS)
            if indicator.agent_status is AgentStatus.IDLE:
                break
        else:
            print("ERROR: the agent did not start")
            return False

        logo_status = app.screen.query_one(WidgetForgeLogo).status
        if str(logo_status.content) != READY_TEXT:
            print("ERROR: the forge logo does not say the agent is ready")
            return False
        print("  logo: the hammer rests, the agent is ready")

        app.screen.query_one(f"#{PROMPT_INPUT_ID}", Input).value = "list the files"
        await pilot.press("enter")

        for _ in range(WAIT_STEPS):
            await pilot.pause(WAIT_STEP_SECONDS)
            if isinstance(app.screen, ModalPermissionScreen):
                break
        else:
            print("ERROR: the permission modal did not show up")
            return False

        modal = app.screen.view_model
        print(f"  modal: {modal.action} -> {modal.summary}")
        await pilot.press(answer)

        for _ in range(WAIT_STEPS):
            await pilot.pause(WAIT_STEP_SECONDS)

        feed = app.screen.query_one(WidgetChatFeed)
        for message in feed.query(WidgetAgentMessage):
            print("  AGENT:", message.content)
        for call in feed.query(WidgetToolCall):
            result = call.result.content if call.result else "—"
            call_line = f"{call.view_model.title} {call.view_model.summary}"
            print(f"  TOOL : {call_line} -> {result}")

        footer = app.screen.query_one(WidgetStatusFooter)
        tokens = footer.query_one("#footer-tokens", Label).content
        status = app.screen.query_one(WidgetWorkingIndicator).agent_status
        print(f"  status: {status.value} | tokens: {tokens}")
        return status is AgentStatus.IDLE


async def wait_until(pilot, condition) -> bool:
    for _ in range(WAIT_STEPS):
        await pilot.pause(WAIT_STEP_SECONDS)
        if condition():
            return True
    return False


async def walk_slash_commands() -> bool:
    container = Container()
    container.wire(modules=["hefajstos.ui.app"])
    app = HefajstosApp()

    async with app.run_test(size=(100, 30)) as pilot:
        indicator = app.screen.query_one(WidgetWorkingIndicator)
        if not await wait_until(
            pilot, lambda: indicator.agent_status is AgentStatus.IDLE
        ):
            print("ERROR: the agent did not start")
            return False

        command_list = app.screen.query_one(WidgetCommandList)
        await pilot.press("/")
        if not await wait_until(pilot, lambda: command_list.option_count == 3):
            print("ERROR: '/' did not list the three built-in commands")
            return False
        print(f"  '/': {command_list.option_count} commands listed")

        await pilot.press("m", "o")
        if not await wait_until(pilot, lambda: command_list.option_count == 1):
            print("ERROR: '/mo' did not narrow the list down to /model")
            return False
        await pilot.press("enter")

        def find_picker() -> WidgetModelPicker | None:
            pickers = app.screen.query(WidgetModelPicker)
            return pickers.first() if pickers else None

        if not await wait_until(pilot, lambda: find_picker() is not None):
            print("ERROR: /model did not open the picker")
            return False
        picker = find_picker()
        assert picker is not None
        prompt = app.screen.query_one(f"#{PROMPT_INPUT_ID}", Input)
        if not prompt.disabled:
            print("ERROR: the prompt stays enabled while the picker is open")
            return False

        await pilot.press("down", "right")
        row = picker.view_model.models[picker.model_index]
        expected = row.to_selection(picker.selected_indexes[picker.model_index])
        print(f"  picker: {expected.model_id} {expected.settings}")
        await pilot.press("enter")

        footer_model = app.screen.query_one("#footer-model", Label)
        if not await wait_until(
            pilot, lambda: str(footer_model.content).startswith(expected.model_id)
        ):
            print(f"ERROR: the footer does not show {expected.model_id}")
            return False
        print(f"  footer: {footer_model.content}")
        if prompt.disabled or not prompt.has_focus:
            print("ERROR: the prompt did not come back after the picker")
            return False

        await pilot.press(*"/model", "enter")
        if not await wait_until(pilot, lambda: find_picker() is not None):
            print("ERROR: /model did not open the picker a second time")
            return False
        await pilot.press("escape")
        if not await wait_until(pilot, lambda: find_picker() is None):
            print("ERROR: escape did not close the picker")
            return False
        if not str(footer_model.content).startswith(expected.model_id):
            print("ERROR: escape changed the model")
            return False
        print("  escape: picker closed, model unchanged")

        feed = app.screen.query_one(WidgetChatFeed)
        await pilot.press(*"/clear", "enter")
        if not await wait_until(pilot, lambda: len(feed.children) == 2):
            print("ERROR: /clear did not leave just the logo and the welcome line")
            return False
        if not feed.query(WidgetForgeLogo):
            print("ERROR: /clear removed the logo")
            return False
        print("  /clear: only the logo and the welcome line are left")

        footer_tokens = app.screen.query_one("#footer-tokens", Label)
        await pilot.press(*"/new", "enter")
        if not await wait_until(
            pilot,
            lambda: len(feed.children) == 3 and str(footer_tokens.content) == "↑0 ↓0",
        ):
            print("ERROR: /new did not leave the intro, one notice and zero tokens")
            return False
        print(
            f"  /new: logo, welcome line and one notice, tokens {footer_tokens.content}"
        )
        return True


async def main() -> int:
    for answer in ("y", "n"):
        print(f"--- turn answered with {answer!r} ---")
        if not await walk_one_turn(answer):
            return 1
    print("--- slash commands ---")
    if not await walk_slash_commands():
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
