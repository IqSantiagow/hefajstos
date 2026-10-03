import logging

from dependency_injector.wiring import Provide, inject
from textual.app import App
from textual.theme import Theme

from hefajstos.containers.main_container import Container
from hefajstos.presentation.chat_repository import ChatRepository
from hefajstos.ui.screens.chat.chat_screen import ChatScreen

logger = logging.getLogger(__name__)

THEME = Theme(
    name="pi-dark",
    dark=True,
    primary="#c49ae6",
    secondary="#8fa6f0",
    accent="#c49ae6",
    success="#6fcf9f",
    error="#f08f7c",
    warning="#d9b25a",
    foreground="#dfe0e3",
    background="#1c1d22",
    surface="#1c1d22",
    panel="#26282e",
)


class HefajstosApp(App):
    CSS_PATH = "css.tcss"
    BINDINGS = [
        ("ctrl+c", "quit"),
    ]

    @inject
    def __init__(
        self,
        chat_repository: ChatRepository = Provide[Container.chat_repository],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.chat_repository = chat_repository

    def on_mount(self) -> None:
        self.register_theme(THEME)
        self.theme = THEME.name
        self.push_screen(ChatScreen(chat_repository=self.chat_repository))

    async def action_quit(self) -> None:
        # Stop the agent first, or the Copilot process outlives the app.
        await self.shutdown_agent()
        self.exit()

    async def on_unmount(self) -> None:
        # For every exit that did not go through action_quit.
        await self.shutdown_agent()

    async def shutdown_agent(self) -> None:
        try:
            await self.chat_repository.shutdown_agent()
        except Exception as e:
            logger.exception("Failed to shut the agent down", exc_info=e)
