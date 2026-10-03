from typing import Protocol

from hefajstos.protocols.command_protocol import CommandProtocol
from hefajstos.services.models.commands import CommandResult


class CommandsProtocol(Protocol):
    def list_matching(self, prefix: str) -> list[CommandProtocol]: ...

    async def run(self, text: str) -> CommandResult: ...
