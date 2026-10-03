import asyncio
import unittest
from unittest.mock import patch

from hefajstos.adapters.stub_agent_adapter import StubAgentAdapter
from hefajstos.services.models.agent_events import (
    AgentText,
    PermissionDecision,
    PermissionRequested,
    TokensUsed,
    ToolStarted,
)
from hefajstos.services.models.model_choice import ModelSelection

READ_TIMEOUT_SECONDS = 1.0


async def play_turn(adapter: StubAgentAdapter, decision: PermissionDecision) -> list:
    """Play one turn and answer the permission request with `decision`."""
    events = []

    async def read_all() -> None:
        async for event in adapter.send_and_stream("list the files"):
            events.append(event)
            if isinstance(event, PermissionRequested):
                adapter.answer_permission(event.request_id, decision)

    await asyncio.wait_for(read_all(), timeout=READ_TIMEOUT_SECONDS)
    return events


class TestStubAgentAdapter(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        patcher = patch("hefajstos.adapters.stub_agent_adapter.WORD_DELAY_SECONDS", 0)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.adapter = StubAgentAdapter(model="stub", working_directory="/tmp")

    async def test_an_approved_turn_runs_the_tool(self) -> None:
        events = await play_turn(self.adapter, PermissionDecision.APPROVE_ONCE)

        self.assertTrue(any(isinstance(event, ToolStarted) for event in events))
        self.assertIsInstance(events[-1], TokensUsed)

    async def test_a_rejected_turn_does_not_run_the_tool(self) -> None:
        events = await play_turn(self.adapter, PermissionDecision.REJECT)

        self.assertFalse(any(isinstance(event, ToolStarted) for event in events))
        self.assertIsInstance(events[-1], TokensUsed)

    async def test_every_message_ends_with_its_full_text(self) -> None:
        events = await play_turn(self.adapter, PermissionDecision.REJECT)

        final_texts = [
            event for event in events if isinstance(event, AgentText) and event.is_final
        ]
        self.assertEqual(2, len(final_texts))

    async def test_abort_ends_the_turn_at_the_permission_request(self) -> None:
        events = []

        async def read_all() -> None:
            async for event in self.adapter.send_and_stream("list the files"):
                events.append(event)
                if isinstance(event, PermissionRequested):
                    await self.adapter.abort()

        await asyncio.wait_for(read_all(), timeout=READ_TIMEOUT_SECONDS)

        self.assertIsInstance(events[-1], PermissionRequested)

    async def test_an_old_request_id_is_not_answered(self) -> None:
        answered = self.adapter.answer_permission(
            "stub-permission-99", PermissionDecision.APPROVE_ONCE
        )

        self.assertFalse(answered)


class TestStubAgentAdapterModels(unittest.IsolatedAsyncioTestCase):
    async def test_the_configured_model_is_listed_first(self) -> None:
        adapter = StubAgentAdapter(model="claude-sonnet-5", working_directory="/tmp")

        models = await adapter.list_models()

        self.assertEqual("claude-sonnet-5", models[0].id)

    async def test_a_stub_model_is_not_listed_twice(self) -> None:
        adapter = StubAgentAdapter(model="stub-small", working_directory="/tmp")

        ids = [model.id for model in await adapter.list_models()]

        self.assertEqual(1, ids.count("stub-small"))

    async def test_offers_a_model_with_settings_and_one_without(self) -> None:
        adapter = StubAgentAdapter(model="stub", working_directory="/tmp")

        settings_counts = {len(model.settings) for model in await adapter.list_models()}

        self.assertIn(0, settings_counts)
        self.assertTrue(any(count > 0 for count in settings_counts))

    async def test_a_switch_updates_the_model_and_its_settings(self) -> None:
        adapter = StubAgentAdapter(model="stub", working_directory="/tmp")

        await adapter.set_model(
            ModelSelection(model_id="stub-large", settings={"reasoning_effort": "max"})
        )

        self.assertEqual("stub-large", adapter.model)
        self.assertEqual({"reasoning_effort": "max"}, adapter.model_settings)
