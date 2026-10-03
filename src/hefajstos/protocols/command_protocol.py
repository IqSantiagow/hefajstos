from typing import Protocol

from hefajstos.services.models.commands import CommandResult, CommandSource


class CommandProtocol(Protocol):
    name: str
    description: str
    source: CommandSource

    async def run(self, arguments: str) -> CommandResult: ...
