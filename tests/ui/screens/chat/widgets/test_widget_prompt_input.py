import unittest

from hefajstos.presentation.view_models.command_view_model import CommandViewModel
from hefajstos.ui.screens.chat.widgets.widget_command_list import describe_command
from hefajstos.ui.screens.chat.widgets.widget_prompt_input import is_command_prefix


class TestIsCommandPrefix(unittest.TestCase):
    def test_a_slash_and_a_partial_name_still_pick_a_command(self) -> None:
        self.assertTrue(is_command_prefix("/"))
        self.assertTrue(is_command_prefix("/mo"))

    def test_a_command_with_arguments_no_longer_picks(self) -> None:
        self.assertFalse(is_command_prefix("/model gpt-5"))

    def test_a_normal_prompt_is_not_a_command(self) -> None:
        self.assertFalse(is_command_prefix("fix the /tmp path"))


class TestDescribeCommand(unittest.TestCase):
    def test_shows_the_slash_name_the_description_and_the_source(self) -> None:
        text = describe_command(
            CommandViewModel(
                name="model", description="Switch the model", source_label="built-in"
            )
        )

        self.assertTrue(text.startswith("/model"))
        self.assertIn("Switch the model", text)
        self.assertTrue(text.endswith("built-in"))
