import asyncio
from typing import Any

from textual.containers import VerticalGroup


class WidgetPanel(VerticalGroup):
    """Shown by WidgetPanelSlot above the prompt; it ends with finish() or cancel().

    Built-in pickers subclass it now, extensions will later.
    """

    can_focus = True

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.__result: asyncio.Future[Any] = asyncio.get_running_loop().create_future()

    def finish(self, result: Any) -> None:
        if not self.__result.done():
            self.__result.set_result(result)

    def cancel(self) -> None:
        """None means the panel was closed without an answer."""
        self.finish(None)

    async def wait_for_result(self) -> Any:
        return await self.__result
