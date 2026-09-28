from textual.reactive import reactive
from textual.timer import Timer
from textual.widgets import Static

from hefajstos.services.models.agent_events import AgentStatus

SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
SPINNER_INTERVAL_SECONDS = 0.08
WORKING_TEXT = "Working… (ctrl+x to abort)"


class WidgetWorkingIndicator(Static):
    """One line above the prompt: a spinner while the agent works, empty otherwise.

    It stays one line high when empty, so the prompt below does not jump.
    """

    agent_status: reactive[AgentStatus] = reactive(AgentStatus.STARTING)

    def __init__(self, **kwargs) -> None:
        super().__init__("", markup=False, **kwargs)
        self.__timer: Timer | None = None
        self.__frame = 0

    def watch_agent_status(self, new_status: AgentStatus) -> None:
        if new_status == AgentStatus.THINKING:
            self.__start_spinner()
        else:
            self.__stop_spinner()

    def __start_spinner(self) -> None:
        if self.__timer is None:
            self.__timer = self.set_interval(
                SPINNER_INTERVAL_SECONDS, self.__show_next_frame
            )
        self.__show_next_frame()

    def __stop_spinner(self) -> None:
        if self.__timer is not None:
            self.__timer.stop()
            self.__timer = None
        self.update("")

    def __show_next_frame(self) -> None:
        self.__frame = (self.__frame + 1) % len(SPINNER_FRAMES)
        self.update(f"{SPINNER_FRAMES[self.__frame]} {WORKING_TEXT}")
