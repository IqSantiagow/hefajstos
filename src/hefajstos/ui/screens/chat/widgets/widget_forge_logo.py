from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup
from textual.content import Content
from textual.style import Style
from textual.timer import Timer
from textual.widgets import Label, Static

from hefajstos.ui.widgets.widget_spinner import WidgetSpinner

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
            yield WidgetSpinner(id="forge-status")

    def on_mount(self) -> None:
        self.tick = 0
        self.timer: Timer = self.set_interval(TICK_SECONDS, self.show_next_tick)
        self.show_next_tick()
        self.status.start(STARTING_TEXT)

    def show_next_tick(self) -> None:
        self.tick += 1
        self.show_drawing(HAMMER_BEAT[self.tick % len(HAMMER_BEAT)])

    def show_ready(self) -> None:
        self.rest_the_hammer(READY_TEXT, status_class="-ready")

    def show_failed(self) -> None:
        self.rest_the_hammer(FAILED_TEXT, status_class="-error")

    def rest_the_hammer(self, status_text: str, status_class: str) -> None:
        self.timer.stop()
        self.show_drawing(HAMMER_DOWN)
        self.status.stop(status_text)
        self.status.add_class(status_class)

    def show_drawing(self, drawing: tuple[str, ...]) -> None:
        self.query_one("#forge-drawing", Static).update(self.paint(drawing))

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

    @property
    def status(self) -> WidgetSpinner:
        return self.query_one("#forge-status", WidgetSpinner)
