from dataclasses import dataclass

from hefajstos.presentation.view_models.chat_item_view_model import NoticeViewModel
from hefajstos.presentation.view_models.footer_view_model import AgentInfoViewModel
from hefajstos.services.models.commands import OpenModelPicker
from hefajstos.services.models.model_choice import ModelChoice, ModelSelection


@dataclass(slots=True)
class ModelSettingViewModel:
    key: str
    label: str
    choices: list[str]
    selected_index: int


@dataclass(slots=True)
class ModelRowViewModel:
    model_id: str
    name: str
    context_window_tokens: int | None
    is_current: bool
    settings: list[ModelSettingViewModel]

    def to_selection(self, selected_indexes: list[int]) -> ModelSelection:
        """selected_indexes goes in the same order as settings."""
        return ModelSelection(
            model_id=self.model_id,
            settings={
                setting.key: setting.choices[index]
                for setting, index in zip(self.settings, selected_indexes)
            },
        )


@dataclass(slots=True)
class ModelPickerViewModel:
    models: list[ModelRowViewModel]
    # The row the picker opens on - the current model, or the first one.
    selected_index: int

    @classmethod
    def from_result(cls, picker: OpenModelPicker) -> "ModelPickerViewModel":
        rows = [
            _build_row(model, picker.current_model_id, picker.current_settings)
            for model in picker.models
        ]
        current = [index for index, row in enumerate(rows) if row.is_current]
        return cls(models=rows, selected_index=current[0] if current else 0)


def _build_row(
    model: ModelChoice, current_model_id: str, current_settings: dict[str, str]
) -> ModelRowViewModel:
    is_current = model.id == current_model_id
    # Another model opens on its first choice - the provider's default.
    chosen = current_settings if is_current else {}
    return ModelRowViewModel(
        model_id=model.id,
        name=model.name,
        context_window_tokens=model.context_window_tokens,
        is_current=is_current,
        settings=[
            ModelSettingViewModel(
                key=setting.key,
                label=setting.label,
                choices=list(setting.choices),
                selected_index=_index_of(setting.choices, chosen.get(setting.key)),
            )
            for setting in model.settings
        ],
    )


def _index_of(choices: list[str], value: str | None) -> int:
    return choices.index(value) if value in choices else 0


@dataclass(slots=True)
class ModelChangedViewModel:
    agent_info: AgentInfoViewModel
    notice: NoticeViewModel
