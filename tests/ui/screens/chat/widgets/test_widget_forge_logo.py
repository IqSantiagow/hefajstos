"""forge_part is a pure function, so it is tested even though it lives next to
the widget that uses it."""

import unittest

from hefajstos.ui.screens.chat.widgets.widget_forge_logo import (
    HAMMER_BEAT,
    STRIKE,
    forge_part,
)


class TestForgePart(unittest.TestCase):
    def test_the_top_row_of_the_anvil_is_its_face(self) -> None:
        self.assertEqual("anvil-face", forge_part(2, "▄"))

    def test_the_rows_below_are_its_body(self) -> None:
        self.assertEqual("anvil-body", forge_part(3, "█"))
        self.assertEqual("anvil-body", forge_part(4, "▄"))

    def test_tells_the_hammer_head_from_the_handle(self) -> None:
        self.assertEqual("hammer-head", forge_part(1, "█"))
        self.assertEqual("hammer-handle", forge_part(1, "━"))
        self.assertEqual("hammer-handle", forge_part(1, "╲"))

    def test_tells_sparks_from_embers(self) -> None:
        self.assertEqual("spark", forge_part(1, "*"))
        self.assertEqual("spark", forge_part(0, "'"))
        self.assertEqual("ember", forge_part(0, "."))


class TestHammerBeat(unittest.TestCase):
    def test_the_hammer_strikes_once_per_beat(self) -> None:
        self.assertEqual(1, HAMMER_BEAT.count(STRIKE))

    def test_every_drawing_has_five_rows(self) -> None:
        for drawing in HAMMER_BEAT:
            self.assertEqual(5, len(drawing))
