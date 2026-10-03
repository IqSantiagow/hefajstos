from textual.content import Content
from textual.widgets import OptionList
from textual.widgets.option_list import Option

from hefajstos.presentation.view_models.command_view_model import CommandViewModel

HIDDEN = "hidden"


def describe_command(command: CommandViewModel) -> str:
    return f"/{command.name:<10} {command.description}  {command.source_label}"


class WidgetCommandList(OptionList):
    can_focus = False

    def show_commands(self, commands: list[CommandViewModel]) -> None:
        self.clear_options()
        self.add_options(
            Option(Content(describe_command(command)), id=command.name)
            for command in commands
        )
        self.set_class(not commands, HIDDEN)
        if commands:
            self.highlighted = 0

    def hide(self) -> None:
        self.clear_options()
        self.add_class(HIDDEN)

    @property
    def is_open(self) -> bool:
        return not self.has_class(HIDDEN)

    @property
    def highlighted_name(self) -> str | None:
        option = self.highlighted_option
        return option.id if option is not None else None
