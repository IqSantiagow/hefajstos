from textual.timer import Timer
from textual.widgets import Static

SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
SPINNER_INTERVAL_SECONDS = 0.08


class WidgetSpinner(Static):
    def __init__(self, **kwargs) -> None:
        super().__init__("", markup=False, **kwargs)
        self.__text = ""
        self.__frame = 0
        self.__timer: Timer | None = None

    def start(self, text: str) -> None:
        self.__text = text
        if self.__timer is None:
            self.__timer = self.set_interval(
                SPINNER_INTERVAL_SECONDS, self.__show_next_frame
            )
        self.__show_next_frame()

    def stop(self, text: str = "") -> None:
        if self.__timer is not None:
            self.__timer.stop()
            self.__timer = None
        self.update(text)

    def __show_next_frame(self) -> None:
        self.__frame = (self.__frame + 1) % len(SPINNER_FRAMES)
        self.update(f"{SPINNER_FRAMES[self.__frame]} {self.__text}")
