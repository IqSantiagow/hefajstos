import unittest

from hefajstos.presentation.view_models.footer_view_model import (
    TokensViewModel,
    describe_model_settings,
)
from hefajstos.services.models.agent_events import TokensUsed
from hefajstos.services.models.model_choice import PROVIDER_DEFAULT


class TestTokensViewModel(unittest.TestCase):
    def test_carries_both_counters(self) -> None:
        tokens = TokensViewModel.from_event(
            TokensUsed(input_tokens=1200, output_tokens=95)
        )

        self.assertEqual(TokensViewModel(input_tokens=1200, output_tokens=95), tokens)


class TestDescribeModelSettings(unittest.TestCase):
    def test_leaves_out_the_providers_default(self) -> None:
        settings = {"reasoning_effort": "high", "context_tier": PROVIDER_DEFAULT}

        self.assertEqual(["high"], describe_model_settings(settings))

    def test_no_settings_describe_as_nothing(self) -> None:
        self.assertEqual([], describe_model_settings({}))
