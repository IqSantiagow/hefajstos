from hefajstos.protocols.command_protocol import CommandProtocol
from hefajstos.services.models.commands import CommandNotice, CommandResult


def parse_command_text(text: str) -> tuple[str, str]:
    name, _, arguments = text.strip().removeprefix("/").partition(" ")
    return name.lower(), arguments.strip()


class CommandsService:
    def __init__(self, commands: list[CommandProtocol]) -> None:
        self.__commands: dict[str, CommandProtocol] = {}
        for command in commands:
            self.add(command)

    def add(self, command: CommandProtocol) -> None:
        taken_by = self.__commands.get(command.name)
        if taken_by is not None:
            raise ValueError(
                f"/{command.name} is already taken by a {taken_by.source} command"
            )
        self.__commands[command.name] = command

    def list_matching(self, prefix: str) -> list[CommandProtocol]:
        name_prefix = prefix.strip().removeprefix("/").lower()
        return sorted(
            (
                command
                for command in self.__commands.values()
                if command.name.startswith(name_prefix)
            ),
            key=lambda command: command.name,
        )

    async def run(self, text: str) -> CommandResult:
        name, arguments = parse_command_text(text)
        command = self.__commands.get(name)
        if command is None:
            return CommandNotice(text=f"Unknown command: /{name}", is_error=True)
        return await command.run(arguments)
