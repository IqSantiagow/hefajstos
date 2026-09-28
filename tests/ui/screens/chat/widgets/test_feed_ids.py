"""The only test under ui/ - feed_ids is a pure function."""

import re
import unittest

from hefajstos.ui.screens.chat.widgets.feed_ids import (
    message_widget_id,
    sanitize_id,
    tool_widget_id,
)

# What Textual accepts as an id: a letter or underscore, then word characters.
TEXTUAL_ID = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_-]*$")


class TestSanitizeId(unittest.TestCase):
    def test_leaves_a_plain_id_untouched(self) -> None:
        self.assertEqual("msg_1-2", sanitize_id("msg_1-2"))

    def test_replaces_characters_a_selector_cannot_contain(self) -> None:
        self.assertEqual("a-b-c-d", sanitize_id("a.b:c/d"))

    def test_falls_back_when_everything_was_stripped(self) -> None:
        self.assertEqual("unknown", sanitize_id(""))


class TestWidgetIds(unittest.TestCase):
    def test_a_message_id_and_a_tool_id_never_collide(self) -> None:
        self.assertNotEqual(message_widget_id("same"), tool_widget_id("same"))

    def test_every_id_is_a_valid_textual_id(self) -> None:
        raw_ids = ["msg_1", "01J8.XYZ/7", "", "tool call #3", "ąćę", "123"]

        for raw_id in raw_ids:
            for widget_id in (message_widget_id(raw_id), tool_widget_id(raw_id)):
                self.assertRegex(
                    widget_id, TEXTUAL_ID, f"{raw_id!r} produced {widget_id!r}"
                )

    def test_the_same_source_id_always_maps_to_the_same_widget_id(self) -> None:
        self.assertEqual(message_widget_id("01J8.XYZ"), message_widget_id("01J8.XYZ"))
