from dataclasses import dataclass

from hefajstos.protocols.command_protocol import CommandProtocol


@dataclass(slots=True)
class CommandViewModel:
    name: str
    description: str
    source_label: str

    @classmethod
    def from_command(cls, command: CommandProtocol) -> "CommandViewModel":
        return cls(
            name=command.name,
            description=command.description,
            source_label=str(command.source),
        )


@dataclass(slots=True)
class ClearFeedViewModel:
    pass
