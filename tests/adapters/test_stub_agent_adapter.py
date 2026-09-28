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
