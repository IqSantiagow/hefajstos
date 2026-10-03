import unittest
from pathlib import Path

from hefajstos.ui.screens.chat.widgets.widget_status_footer import (
    format_token_count,
    shorten_home,
)


class TestShortenHome(unittest.TestCase):
    def test_replaces_the_home_directory_with_a_tilde(self) -> None:
        directory = str(Path.home() / "Projects" / "foo")

        self.assertEqual("~/Projects/foo", shorten_home(directory))

    def test_the_home_directory_itself_becomes_a_bare_tilde(self) -> None:
        self.assertEqual("~", shorten_home(str(Path.home())))

    def test_leaves_a_path_outside_home_alone(self) -> None:
        self.assertEqual("/opt/work", shorten_home("/opt/work"))

    def test_does_not_shorten_a_sibling_that_merely_shares_the_prefix(self) -> None:
        sibling = str(Path.home()) + "-backup/foo"

        self.assertEqual(sibling, shorten_home(sibling))


class TestFormatTokenCount(unittest.TestCase):
    def test_leaves_numbers_below_a_thousand_alone(self) -> None:
        self.assertEqual("0", format_token_count(0))
        self.assertEqual("999", format_token_count(999))

    def test_shows_one_decimal_below_ten_thousand(self) -> None:
        self.assertEqual("1.3k", format_token_count(1284))

    def test_rounds_to_whole_thousands_below_a_million(self) -> None:
        self.assertEqual("45k", format_token_count(45_300))

    def test_shows_one_decimal_below_ten_million(self) -> None:
        self.assertEqual("1.2M", format_token_count(1_200_000))

    def test_rounds_to_whole_millions_above_that(self) -> None:
        self.assertEqual("12M", format_token_count(12_400_000))
