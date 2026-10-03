import asyncio
from typing import Any

from textual.containers import VerticalGroup

from hefajstos.ui.widgets.widget_panel import WidgetPanel


class WidgetPanelSlot(VerticalGroup):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.__lock = asyncio.Lock()

    async def show(self, panel: WidgetPanel) -> Any:
        async with self.__lock:
            await self.mount(panel)
            panel.focus()
            try:
                return await panel.wait_for_result()
            finally:
                await panel.remove()
