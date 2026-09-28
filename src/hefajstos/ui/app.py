import logging

from dependency_injector.wiring import Provide, inject
from textual.app import App

from hefajstos.containers.main_container import Container
from hefajstos.presentation.chat_repository import ChatRepository
from hefajstos.ui.screens.chat.chat_screen import ChatScreen

logger = logging.getLogger(__name__)

THEME = "gruvbox"


class HefajstosApp(App):
    CSS_PATH = "css.tcss"
    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
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
        self.theme = THEME
        self.push_screen(ChatScreen(chat_repository=self.chat_repository))

    async def action_quit(self) -> None:
        """Stop the agent first, or the Copilot process outlives the app."""
        await self.shutdown_agent()
        self.exit()

    async def on_unmount(self) -> None:
        """For every exit that did not go through action_quit."""
        await self.shutdown_agent()

    async def shutdown_agent(self) -> None:
        try:
            await self.chat_repository.shutdown_agent()
        except Exception as e:
            logger.exception("Failed to shut the agent down", exc_info=e)
