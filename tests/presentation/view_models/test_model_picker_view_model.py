import unittest

from hefajstos.presentation.view_models.model_picker_view_model import (
    ModelPickerViewModel,
)
from hefajstos.services.models.commands import OpenModelPicker
from hefajstos.services.models.model_choice import (
    PROVIDER_DEFAULT,
    ModelChoice,
    ModelSelection,
    ModelSetting,
)

EFFORT = ModelSetting(
    key="reasoning_effort",
    label="Reasoning effort",
    choices=[PROVIDER_DEFAULT, "low", "high"],
)
CONTEXT = ModelSetting(
    key="context_tier", label="Context", choices=[PROVIDER_DEFAULT, "long_context"]
)


def make_model(**overrides) -> ModelChoice:
    defaults = dict(
        id="gpt-5",
        name="GPT-5",
        context_window_tokens=400_000,
        settings=[EFFORT, CONTEXT],
    )
    defaults.update(overrides)
    return ModelChoice(**defaults)  # type: ignore[arg-type]


def make_picker(**overrides) -> ModelPickerViewModel:
    defaults = dict(
        models=[make_model(id="auto", settings=[]), make_model(id="gpt-5")],
        current_model_id="gpt-5",
        current_settings={"reasoning_effort": "high"},
    )
    defaults.update(overrides)
    return ModelPickerViewModel.from_result(OpenModelPicker(**defaults))  # type: ignore[arg-type]


class TestModelPickerViewModel(unittest.TestCase):
    def test_opens_on_the_current_model(self) -> None:
        picker = make_picker()

        self.assertEqual(1, picker.selected_index)
        self.assertTrue(picker.models[1].is_current)
        self.assertFalse(picker.models[0].is_current)

    def test_opens_on_the_first_model_when_the_current_one_is_not_listed(
        self,
    ) -> None:
        self.assertEqual(0, make_picker(current_model_id="gone").selected_index)

    def test_the_current_model_shows_its_current_settings(self) -> None:
        effort, context = make_picker().models[1].settings

        self.assertEqual("high", effort.choices[effort.selected_index])
        self.assertEqual(PROVIDER_DEFAULT, context.choices[context.selected_index])

    def test_another_model_opens_on_the_providers_default(self) -> None:
        picker = make_picker(models=[make_model(id="gpt-5"), make_model(id="gpt-5.4")])

        effort = picker.models[1].settings[0]

        self.assertEqual(0, effort.selected_index)

    def test_a_current_value_the_model_does_not_offer_falls_back_to_default(
        self,
    ) -> None:
        picker = make_picker(current_settings={"reasoning_effort": "max"})

        self.assertEqual(0, picker.models[1].settings[0].selected_index)

    def test_an_empty_model_list_opens_on_nothing(self) -> None:
        picker = make_picker(models=[])

        self.assertEqual([], picker.models)
        self.assertEqual(0, picker.selected_index)


class TestModelRowToSelection(unittest.TestCase):
    def test_builds_the_selection_from_the_picked_indexes(self) -> None:
        row = make_picker().models[1]

        selection = row.to_selection([2, 1])

        self.assertEqual(
            ModelSelection(
                model_id="gpt-5",
                settings={"reasoning_effort": "high", "context_tier": "long_context"},
            ),
            selection,
        )

    def test_a_model_without_settings_gives_empty_settings(self) -> None:
        row = make_picker().models[0]

        self.assertEqual(
            ModelSelection(model_id="auto", settings={}), row.to_selection([])
        )
