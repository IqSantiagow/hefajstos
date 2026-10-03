from hefajstos.presentation.view_models.command_view_model import CommandViewModel
from hefajstos.protocols.commands_protocol import CommandsProtocol


class ListCommandsUseCase:
    def __init__(self, commands_protocol: CommandsProtocol) -> None:
        self.commands_protocol = commands_protocol

    def __call__(self, prefix: str) -> list[CommandViewModel]:
        return [
            CommandViewModel.from_command(command)
            for command in self.commands_protocol.list_matching(prefix)
        ]
