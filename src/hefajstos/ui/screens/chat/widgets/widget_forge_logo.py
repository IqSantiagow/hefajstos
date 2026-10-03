from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup
from textual.content import Content
from textual.style import Style
from textual.timer import Timer
from textual.widgets import Label, Static

from hefajstos.ui.screens.chat.widgets.widget_working_indicator import SPINNER_FRAMES

TITLE = "H E F A J S T O S"
TAGLINE = "coding agent · github copilot sdk"
STARTING_TEXT = "starting the agent…"
READY_TEXT = "● ready"
FAILED_TEXT = "✕ the agent did not start"

TICK_SECONDS = 0.1

ANVIL = (
    "▄▄▄▄▄▄▄▄▄▄▄",
    " ▀▀▀██████▀",
    "    ▄████▄",
)
HAMMER_UP = (
    "    ▐█▌",
    "       ╲",
    *ANVIL,
)
HAMMER_DOWN = (
    "",
    "   ▐█▌━━━━",
    *ANVIL,
)
STRIKE = (
    " .        '",
    "  *▐█▌━━━━",
    *ANVIL,
)

# One drawing per tick.
HAMMER_BEAT = (
    HAMMER_UP,
    HAMMER_UP,
    HAMMER_UP,
    HAMMER_UP,
    STRIKE,
    HAMMER_DOWN,
    HAMMER_UP,
    HAMMER_UP,
)


def forge_part(row_number: int, character: str) -> str:
    """Which part of the drawing a character is. Its colour is in ui/css.tcss."""
    if row_number == 2:
        return "anvil-face"
    if row_number > 2:
        return "anvil-body"
    if character in "▐█▌":
        return "hammer-head"
    if character in "━╲":
        return "hammer-handle"
    if character == ".":
        return "ember"
    return "spark"


class WidgetForgeLogo(HorizontalGroup):
    DEFAULT_CLASSES = "chat-entry"
    COMPONENT_CLASSES = {
        "forge--anvil-face",
        "forge--anvil-body",
        "forge--hammer-head",
        "forge--hammer-handle",
        "forge--spark",
        "forge--ember",
    }

    def compose(self) -> ComposeResult:
        yield Static("", id="forge-drawing", markup=False)
        with VerticalGroup(classes="forge-text"):
            yield Label(TITLE, classes="forge-title", markup=False)
            yield Label(TAGLINE, classes="forge-tagline", markup=False)
            yield Label("", id="forge-status", markup=False)

    def on_mount(self) -> None:
        self.tick = 0
        self.timer: Timer = self.set_interval(TICK_SECONDS, self.show_next_tick)
        self.show_next_tick()

    def show_next_tick(self) -> None:
        self.tick += 1
        drawing = HAMMER_BEAT[self.tick % len(HAMMER_BEAT)]
        spinner = SPINNER_FRAMES[self.tick % len(SPINNER_FRAMES)]
        self.show(drawing, f"{spinner} {STARTING_TEXT}")

    def show_ready(self) -> None:
        self.timer.stop()
        self.show(HAMMER_DOWN, READY_TEXT, status_class="-ready")

    def show_failed(self) -> None:
        self.timer.stop()
        self.show(HAMMER_DOWN, FAILED_TEXT, status_class="-error")

    def show(
        self, drawing: tuple[str, ...], status_text: str, status_class: str = ""
    ) -> None:
        self.query_one("#forge-drawing", Static).update(self.paint(drawing))
        status = self.query_one("#forge-status", Label)
        status.update(status_text)
        status.set_classes(status_class)

    def paint(self, drawing: tuple[str, ...]) -> Content:
        pieces: list[str | tuple[str, Style]] = []
        for row_number, line in enumerate(drawing):
            if row_number > 0:
                pieces.append("\n")
            for character in line:
                if character == " ":
                    pieces.append(character)
                else:
                    part = forge_part(row_number, character)
                    style = self.get_visual_style(f"forge--{part}", partial=True)
                    pieces.append((character, style))
        return Content.assemble(*pieces)
