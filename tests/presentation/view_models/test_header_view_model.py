import unittest
from pathlib import Path

from hefajstos.presentation.view_models.header_view_model import (
    STATUS_LABELS,
    AgentInfoViewModel,
    TokensViewModel,
    format_thousands,
    shorten_home,
)
from hefajstos.services.models.agent_events import AgentStatus, TokensUsed


class TestHeaderViewModels(unittest.TestCase):
    def test_every_status_has_a_label(self) -> None:
        for status in AgentStatus:
            self.assertTrue(STATUS_LABELS.get(status), f"{status} has no label")

    def test_agent_info_shortens_the_home_directory(self) -> None:
        agent_info = AgentInfoViewModel.from_agent(
            model="gpt-5-mini", working_directory=str(Path.home() / "foo")
        )

        self.assertEqual(
            AgentInfoViewModel(model_text="gpt-5-mini", directory_text="~/foo"),
            agent_info,
        )

    def test_formats_both_token_counters(self) -> None:
        tokens = TokensViewModel.from_event(
            TokensUsed(input_tokens=1200, output_tokens=95)
        )

        self.assertEqual("↑ 1 200 / ↓ 95", tokens.text)


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


class TestFormatThousands(unittest.TestCase):
    def test_groups_thousands_with_a_space(self) -> None:
        self.assertEqual("1 284", format_thousands(1284))

    def test_leaves_small_numbers_alone(self) -> None:
        self.assertEqual("0", format_thousands(0))
