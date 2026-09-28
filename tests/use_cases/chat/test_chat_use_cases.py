import unittest
from collections.abc import AsyncGenerator

from hefajstos.presentation.view_models.chat_item_view_model import (
    AgentTextViewModel,
    AutoApprovedViewModel,
    ToolCallViewModel,
)
from hefajstos.presentation.view_models.footer_view_model import TokensViewModel
from hefajstos.presentation.view_models.permission_view_model import PermissionViewModel
from hefajstos.services.models.agent_events import (
    AgentEvent,
    AgentStatus,
    AgentText,
    PermissionDecision,
    PermissionRequested,
    TokensUsed,
    ToolStarted,
    TurnFinished,
)
from hefajstos.use_cases.chat.abort_turn_use_case import AbortTurnUseCase
from hefajstos.use_cases.chat.answer_permission_use_case import (
    AnswerPermissionUseCase,
)
from hefajstos.use_cases.chat.send_message_use_case import SendMessageUseCase
from hefajstos.use_cases.chat.shutdown_agent_use_case import ShutdownAgentUseCase
from hefajstos.use_cases.chat.start_agent_use_case import StartAgentUseCase
from hefajstos.use_cases.chat.stream_agent_responses_use_case import (
    StreamAgentResponsesUseCase,
)


class FakeAgent:
    """Implements AgentProtocol with canned data."""

    def __init__(
        self,
        items: list[AgentStatus | AgentEvent] | None = None,
        answer_result: bool = True,
    ) -> None:
        self.model = "gpt-5"
        self.working_directory = "/opt/project"
        self.items = items or []
        self.answer_result = answer_result
        self.started = False
        self.was_shut_down = False
        self.queued_prompts: list[str] = []
        self.answers: list[tuple[str, PermissionDecision]] = []
        self.aborts = 0

    async def start(self) -> None:
        self.started = True

    async def shutdown(self) -> None:
        self.was_shut_down = True

    def add_prompt_to_queue(self, prompt: str) -> None:
        self.queued_prompts.append(prompt)

    async def consume_prompt_queue(
        self,
    ) -> AsyncGenerator[AgentStatus | AgentEvent, None]:
        for item in self.items:
            yield item

    def answer_permission(self, request_id: str, decision: PermissionDecision) -> bool:
        self.answers.append((request_id, decision))
        return self.answer_result

    async def abort_turn(self) -> None:
        self.aborts += 1


def make_permission(**overrides) -> PermissionRequested:
    defaults = dict(
        request_id="req-1",
        action="run command",
        summary="ls",
        detail="",
        requires_manual_approval=False,
    )
    defaults.update(overrides)
    return PermissionRequested(**defaults)  # type: ignore[arg-type]


class TestLifecycleUseCases(unittest.IsolatedAsyncioTestCase):
    async def test_start_starts_the_agent(self) -> None:
        agent = FakeAgent()

        await StartAgentUseCase(agent_protocol=agent)()

        self.assertTrue(agent.started)

    async def test_start_returns_what_the_footer_shows(self) -> None:
        agent_info = await StartAgentUseCase(agent_protocol=FakeAgent())()

        self.assertEqual("gpt-5", agent_info.model)
        self.assertEqual("/opt/project", agent_info.working_directory)

    async def test_shutdown_shuts_the_agent_down(self) -> None:
        agent = FakeAgent()

        await ShutdownAgentUseCase(agent_protocol=agent)()

        self.assertTrue(agent.was_shut_down)

    async def test_abort_turn_aborts_the_agent(self) -> None:
        agent = FakeAgent()

        await AbortTurnUseCase(agent_protocol=agent)()

        self.assertEqual(1, agent.aborts)


class TestCommandUseCases(unittest.TestCase):
    def test_send_message_puts_the_prompt_in_the_queue(self) -> None:
        agent = FakeAgent()

        SendMessageUseCase(agent_protocol=agent)("fix the tests")

        self.assertEqual(["fix the tests"], agent.queued_prompts)

    def test_answer_permission_passes_the_decision_through(self) -> None:
        agent = FakeAgent()

        AnswerPermissionUseCase(agent_protocol=agent)(
            "req-7", PermissionDecision.REJECT
        )

        self.assertEqual([("req-7", PermissionDecision.REJECT)], agent.answers)

    def test_answer_permission_reports_a_request_that_is_gone(self) -> None:
        agent = FakeAgent(answer_result=False)

        answered = AnswerPermissionUseCase(agent_protocol=agent)(
            "req-gone", PermissionDecision.APPROVE_ONCE
        )

        self.assertFalse(answered)


class TestStreamAgentResponsesUseCase(unittest.IsolatedAsyncioTestCase):
    async def read_all(self, items: list) -> list:
        use_case = StreamAgentResponsesUseCase(agent_protocol=FakeAgent(items=items))
        return [item async for item in use_case()]

    async def test_a_status_passes_through_unchanged(self) -> None:
        items = await self.read_all([AgentStatus.THINKING, AgentStatus.IDLE])

        self.assertEqual([AgentStatus.THINKING, AgentStatus.IDLE], items)

    async def test_feed_events_become_view_models(self) -> None:
        items = await self.read_all(
            [
                AgentText(message_id="m1", text="hi", is_final=False),
                ToolStarted(
                    tool_call_id="c1", tool_name="execute", arguments={"command": "ls"}
                ),
            ]
        )

        self.assertEqual(
            [AgentTextViewModel, ToolCallViewModel], [type(item) for item in items]
        )

    async def test_tokens_become_the_footer_text(self) -> None:
        items = await self.read_all([TokensUsed(input_tokens=1200, output_tokens=95)])

        self.assertEqual([TokensViewModel(input_tokens=1200, output_tokens=95)], items)

    async def test_a_permission_request_becomes_the_modal(self) -> None:
        items = await self.read_all([make_permission(request_id="req-3")])

        self.assertEqual(1, len(items))
        self.assertIsInstance(items[0], PermissionViewModel)
        self.assertEqual("req-3", items[0].request_id)

    async def test_an_auto_approved_request_is_not_a_modal(
        self,
    ) -> None:
        items = await self.read_all([make_permission(auto_approved=True)])

        self.assertEqual(1, len(items))
        self.assertIsInstance(items[0], AutoApprovedViewModel)

    async def test_drops_events_the_screen_does_not_show(self) -> None:
        self.assertEqual([], await self.read_all([TurnFinished()]))
