import unittest

from hefajstos.presentation.view_models.footer_view_model import TokensViewModel
from hefajstos.services.models.agent_events import TokensUsed


class TestTokensViewModel(unittest.TestCase):
    def test_carries_both_counters(self) -> None:
        tokens = TokensViewModel.from_event(
            TokensUsed(input_tokens=1200, output_tokens=95)
        )

        self.assertEqual(TokensViewModel(input_tokens=1200, output_tokens=95), tokens)
