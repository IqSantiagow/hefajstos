import unittest

from hefajstos.presentation.view_models.model_picker_view_model import (
    ModelRowViewModel,
    ModelSettingViewModel,
)
from hefajstos.ui.screens.chat.widgets.widget_model_picker import (
    NO_SETTINGS_TEXT,
    describe_model_row,
    describe_settings,
)


def make_row(**overrides) -> ModelRowViewModel:
    defaults = dict(
        model_id="gpt-5",
        name="GPT-5",
        context_window_tokens=400_000,
        is_current=False,
        settings=[
            ModelSettingViewModel(
                key="reasoning_effort",
                label="Reasoning effort",
                choices=["default", "low", "high"],
                selected_index=2,
            ),
            ModelSettingViewModel(
                key="context_tier",
                label="Context",
                choices=["default", "long_context"],
                selected_index=0,
            ),
        ],
    )
    defaults.update(overrides)
    return ModelRowViewModel(**defaults)  # type: ignore[arg-type]


class TestDescribeModelRow(unittest.TestCase):
    def test_shows_the_name_and_the_context_window(self) -> None:
        text = describe_model_row(make_row())

        self.assertTrue(text.startswith("GPT-5"))
        self.assertTrue(text.endswith("400k"))

    def test_marks_the_current_model(self) -> None:
        self.assertTrue(
            describe_model_row(make_row(is_current=True)).endswith("current")
        )

    def test_a_model_without_a_known_window_shows_only_the_name(self) -> None:
        text = describe_model_row(make_row(context_window_tokens=None))

        self.assertEqual("GPT-5", text)


class TestDescribeSettings(unittest.TestCase):
    def test_one_line_per_setting_with_the_picked_value(self) -> None:
        lines = describe_settings(make_row(), [2, 1], active_setting=0).splitlines()

        self.assertEqual(2, len(lines))
        self.assertIn("‹ high ›", lines[0])
        self.assertIn("‹ long_context ›", lines[1])

    def test_marks_the_setting_that_left_and_right_change(self) -> None:
        lines = describe_settings(make_row(), [0, 0], active_setting=1).splitlines()

        self.assertTrue(lines[1].startswith("›"))
        self.assertFalse(lines[0].startswith("›"))

    def test_a_model_without_settings_says_so(self) -> None:
        text = describe_settings(make_row(settings=[]), [], active_setting=0)

        self.assertEqual(NO_SETTINGS_TEXT, text)
