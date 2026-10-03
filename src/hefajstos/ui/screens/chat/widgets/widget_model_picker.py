from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widgets import Static

from hefajstos.presentation.view_models.model_picker_view_model import (
    ModelPickerViewModel,
    ModelRowViewModel,
)
from hefajstos.ui.screens.chat.widgets.widget_status_footer import format_token_count
from hefajstos.ui.widgets.widget_panel import WidgetPanel

KEY_HINT = "↑↓ model · tab next setting · ←→ change · enter apply · esc cancel"
NO_SETTINGS_TEXT = "This model has no settings."
NO_MODELS_TEXT = "The provider returned no models."

# CSS classes - they have to match ui/css.tcss.
MODEL_ROW = "picker-row"
SELECTED_ROW = "-selected"


def describe_model_row(row: ModelRowViewModel) -> str:
    """'Claude Sonnet 5.5              1M  current'."""
    context = (
        format_token_count(row.context_window_tokens)
        if row.context_window_tokens
        else ""
    )
    current = "current" if row.is_current else ""
    return f"{row.name:<28} {context:>5}  {current}".rstrip()


def describe_settings(
    row: ModelRowViewModel, selected_indexes: list[int], active_setting: int
) -> str:
    """One line per setting; the one ←→ changes is marked with '›'."""
    if not row.settings:
        return NO_SETTINGS_TEXT
    lines = []
    for index, (setting, selected) in enumerate(zip(row.settings, selected_indexes)):
        marker = "›" if index == active_setting else " "
        lines.append(f"{marker} {setting.label:<18} ‹ {setting.choices[selected]} ›")
    return "\n".join(lines)


class WidgetModelPicker(WidgetPanel):
    """Finishes with a ModelSelection, or None on escape."""

    BINDINGS = [
        Binding("up", "move_model(-1)", show=False),
        Binding("down", "move_model(1)", show=False),
        Binding("tab", "next_setting", show=False),
        Binding("left", "change_setting(-1)", show=False),
        Binding("right", "change_setting(1)", show=False),
        Binding("enter", "apply", show=False),
        Binding("escape", "cancel", show=False),
    ]

    def __init__(self, view_model: ModelPickerViewModel, **kwargs) -> None:
        super().__init__(**kwargs)
        self.view_model = view_model
        self.model_index = view_model.selected_index
        self.setting_index = 0
        # Every model keeps what was picked for it while the picker is open.
        self.selected_indexes = [
            [setting.selected_index for setting in row.settings]
            for row in view_model.models
        ]

    def compose(self) -> ComposeResult:
        yield Static("Select a model", markup=False, classes="picker-title")
        with VerticalScroll(classes="picker-models", can_focus=False):
            for row in self.view_model.models:
                yield Static(describe_model_row(row), markup=False, classes=MODEL_ROW)
        yield Static("", markup=False, classes="picker-settings")
        yield Static(KEY_HINT, markup=False, classes="picker-hint")

    def on_mount(self) -> None:
        self.__show_selection()

    def action_move_model(self, step: int) -> None:
        if not self.view_model.models:
            return
        self.model_index = (self.model_index + step) % len(self.view_model.models)
        self.setting_index = 0
        self.__show_selection()

    def action_next_setting(self) -> None:
        settings = self.__settings_count()
        if settings:
            self.setting_index = (self.setting_index + 1) % settings
            self.__show_selection()

    def action_change_setting(self, step: int) -> None:
        if not self.__settings_count():
            return
        row = self.view_model.models[self.model_index]
        choices = row.settings[self.setting_index].choices
        selected = self.selected_indexes[self.model_index]
        selected[self.setting_index] = (selected[self.setting_index] + step) % len(
            choices
        )
        self.__show_selection()

    def action_apply(self) -> None:
        if not self.view_model.models:
            self.cancel()
            return
        row = self.view_model.models[self.model_index]
        self.finish(row.to_selection(self.selected_indexes[self.model_index]))

    def action_cancel(self) -> None:
        self.cancel()

    def __settings_count(self) -> int:
        if not self.view_model.models:
            return 0
        return len(self.view_model.models[self.model_index].settings)

    def __show_selection(self) -> None:
        settings = self.query_one(".picker-settings", Static)
        if not self.view_model.models:
            settings.update(NO_MODELS_TEXT)
            return

        rows = list(self.query(f".{MODEL_ROW}"))
        for index, widget in enumerate(rows):
            widget.set_class(index == self.model_index, SELECTED_ROW)
        self.query_one(".picker-models", VerticalScroll).scroll_to_widget(
            rows[self.model_index], animate=False
        )

        settings.update(
            describe_settings(
                self.view_model.models[self.model_index],
                self.selected_indexes[self.model_index],
                self.setting_index,
            )
        )
