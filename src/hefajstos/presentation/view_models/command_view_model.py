from dataclasses import dataclass

from hefajstos.presentation.view_models.chat_item_view_model import NoticeViewModel
from hefajstos.presentation.view_models.footer_view_model import TokensViewModel
from hefajstos.protocols.command_protocol import CommandProtocol

NEW_SESSION_MESSAGE = "New session - the agent starts with a clean history."


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


@dataclass(slots=True)
class NewSessionViewModel:
    tokens: TokensViewModel
    notice: NoticeViewModel

    @classmethod
    def started(cls) -> "NewSessionViewModel":
        return cls(
            tokens=TokensViewModel(input_tokens=0, output_tokens=0),
            notice=NoticeViewModel(content=NEW_SESSION_MESSAGE, is_error=False),
        )
