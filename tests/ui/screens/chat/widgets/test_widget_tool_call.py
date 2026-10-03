import unittest

from hefajstos.ui.screens.chat.widgets.widget_tool_call import preview_tool_output


class TestPreviewToolOutput(unittest.TestCase):
    def test_leaves_a_short_output_alone(self) -> None:
        self.assertEqual("a\nb", preview_tool_output("a\nb", max_lines=2))

    def test_cuts_a_long_output_and_says_how_much_is_hidden(self) -> None:
        preview = preview_tool_output("a\nb\nc\nd", max_lines=2)

        self.assertEqual("a\nb\n… 2 more lines (click to expand)", preview)

    def test_leaves_an_empty_output_alone(self) -> None:
        self.assertEqual("", preview_tool_output(""))
