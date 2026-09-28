import asyncio
import unittest
from typing import Any
from unittest.mock import patch

from copilot.rpc import (
    PermissionDecisionApproveForSession,
    PermissionDecisionApproveOnce,
    PermissionDecisionReject,
    PermissionDecisionUserNotAvailable,
)
from copilot.generated.session_events import PermissionRequestRead

from hefajstos.adapters.copilot_agent_adapter import (
    REJECTED_BY_USER_FEEDBACK,
    CopilotAgentAdapter,
    _to_copilot_decision,
)
from hefajstos.services.models.agent_events import (
    AgentError,
    AgentText,
    PermissionDecision,
    PermissionRequested,
)
from tests.agent_event_fixtures import (
    make_session_error,
    make_session_idle,
    make_text_delta,
)

STREAM_TIMEOUT_SECONDS = 1.0


class FakeSession:
    """Plays `events_on_send` through the SDK callback whenever a prompt is sent."""

    def __init__(self) -> None:
        self.handler: Any = None
        self.unsubscribed = False
        self.sent_prompts: list[str] = []
        self.calls: list[str] = []
        self.events_on_send: list = []

    def on(self, handler) -> Any:
        self.handler = handler
        return self.unsubscribe

    def unsubscribe(self) -> None:
        self.unsubscribed = True

    async def send(self, prompt: str) -> None:
        self.sent_prompts.append(prompt)
        for event in self.events_on_send:
            self.handler(event)

    async def abort(self) -> None:
        self.calls.append("abort")

    async def disconnect(self) -> None:
        self.calls.append("disconnect")

    def emit(self, event) -> None:
        self.handler(event)


class FakeModel:
    def __init__(self, model_id: str) -> None:
        self.id = model_id


class FakeClient:
    def __init__(self, *args, **kwargs) -> None:
        self.kwargs = kwargs
        self.session = FakeSession()
        self.create_session_kwargs: dict[str, Any] = {}
        self.stopped = False
        self.models = [FakeModel("auto"), FakeModel("claude-sonnet-5")]
        self.list_models_failure: Exception | None = None

    async def start(self) -> None:
        pass

    async def list_models(self) -> list[FakeModel]:
        if self.list_models_failure is not None:
            raise self.list_models_failure
        return self.models

    async def create_session(self, **kwargs) -> FakeSession:
        self.create_session_kwargs = kwargs
        return self.session

    async def stop(self) -> None:
        self.stopped = True


def make_read_request(**overrides) -> PermissionRequestRead:
    defaults = dict(intention="Read the config", path="config.yaml")
    defaults.update(overrides)
    return PermissionRequestRead(**defaults)  # type: ignore[arg-type]


class CopilotAgentAdapterTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.clients: list[FakeClient] = []

        def build_client(*args, **kwargs) -> FakeClient:
            client = FakeClient(*args, **kwargs)
            self.clients.append(client)
            return client

        patcher = patch(
            "hefajstos.adapters.copilot_agent_adapter.CopilotClient",
            side_effect=build_client,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        self.adapter = CopilotAgentAdapter(
            model="auto",
            working_directory="/tmp/project",
            permission_timeout_seconds=60,
        )

    @property
    def client(self) -> FakeClient:
        return self.clients[0]

    @property
    def session(self) -> FakeSession:
        return self.client.session

    async def next_event(self, stream) -> Any:
        return await asyncio.wait_for(
            stream.__anext__(), timeout=STREAM_TIMEOUT_SECONDS
        )

    def ask_for_permission(self, request=None) -> asyncio.Task:
        handler = self.client.create_session_kwargs["on_permission_request"]
        return asyncio.create_task(
            handler(request or make_read_request(), {"session_id": "s1"})
        )


class TestCopilotAgentAdapterStart(CopilotAgentAdapterTestCase):
    async def test_opens_a_streaming_session_with_the_configured_model(self) -> None:
        await self.adapter.start()

        self.assertEqual("auto", self.client.create_session_kwargs["model"])
        self.assertTrue(self.client.create_session_kwargs["streaming"])

    async def test_passes_the_working_directory_to_both_the_client_and_the_session(
        self,
    ) -> None:
        await self.adapter.start()

        self.assertEqual("/tmp/project", self.client.kwargs["working_directory"])
        self.assertEqual(
            "/tmp/project", self.client.create_session_kwargs["working_directory"]
        )

    async def test_refuses_to_send_before_it_was_started(self) -> None:
        with self.assertRaises(RuntimeError):
            await self.adapter.send_and_stream("anything").__anext__()


class TestCopilotAgentAdapterModelCheck(CopilotAgentAdapterTestCase):
    async def test_a_model_that_does_not_exist_fails_with_the_real_names(self) -> None:
        self.adapter.model = "gpt-5"

        with self.assertRaises(ValueError) as raised:
            await self.adapter.start()

        self.assertIn("gpt-5", str(raised.exception))
        self.assertIn("claude-sonnet-5", str(raised.exception))

    async def test_a_model_that_exists_is_accepted(self) -> None:
        self.adapter.model = "claude-sonnet-5"

        await self.adapter.start()

        self.assertEqual("claude-sonnet-5", self.client.create_session_kwargs["model"])

    async def test_an_unreachable_model_list_does_not_block_the_start(self) -> None:
        def build_failing_client(*args, **kwargs) -> FakeClient:
            client = FakeClient(*args, **kwargs)
            client.list_models_failure = RuntimeError("no connection")
            self.clients.append(client)
            return client

        with patch(
            "hefajstos.adapters.copilot_agent_adapter.CopilotClient",
            side_effect=build_failing_client,
        ):
            with self.assertLogs(
                "hefajstos.adapters.copilot_agent_adapter", level="WARNING"
            ):
                await self.adapter.start()

        self.assertIsNotNone(self.client.create_session_kwargs)


class TestCopilotAgentAdapterSendAndStream(CopilotAgentAdapterTestCase):
    async def read_turn(self, prompt: str = "fix the tests") -> list:
        async def read_all() -> list:
            return [event async for event in self.adapter.send_and_stream(prompt)]

        return await asyncio.wait_for(read_all(), timeout=STREAM_TIMEOUT_SECONDS)

    async def test_sends_the_prompt(self) -> None:
        await self.adapter.start()
        self.session.events_on_send = [make_session_idle()]

        await self.read_turn("fix the tests")

        self.assertEqual(["fix the tests"], self.session.sent_prompts)

    async def test_yields_events_in_order_until_the_session_is_idle(self) -> None:
        await self.adapter.start()
        self.session.events_on_send = [
            make_text_delta(delta_content="a", message_id="m1"),
            make_text_delta(delta_content="b", message_id="m1"),
            make_session_idle(),
            make_text_delta(delta_content="after idle", message_id="m2"),
        ]

        events = await self.read_turn()

        self.assertEqual(
            [
                AgentText(message_id="m1", text="a", is_final=False),
                AgentText(message_id="m1", text="b", is_final=False),
            ],
            events,
        )

    async def test_an_error_ends_the_turn(self) -> None:
        await self.adapter.start()
        self.session.events_on_send = [make_session_error(message="rate limit")]

        events = await self.read_turn()

        self.assertEqual([AgentError(message="rate limit")], events)

    async def test_leftovers_from_an_earlier_turn_do_not_end_the_next_one(
        self,
    ) -> None:
        await self.adapter.start()
        self.session.events_on_send = [make_session_error(), make_session_idle()]
        await self.read_turn()
        await asyncio.sleep(0)
        self.session.events_on_send = [
            make_text_delta(delta_content="new", message_id="m2"),
            make_session_idle(),
        ]

        events = await self.read_turn()

        self.assertEqual(
            [AgentText(message_id="m2", text="new", is_final=False)], events
        )

    async def test_an_event_we_do_not_use_is_dropped(self) -> None:
        await self.adapter.start()
        unused = make_text_delta()
        unused.data = object()  # type: ignore[assignment]
        self.session.events_on_send = [unused, make_session_idle()]

        self.assertEqual([], await self.read_turn())

    async def test_a_broken_event_does_not_escape_into_the_sdk(self) -> None:
        await self.adapter.start()

        with self.assertLogs("hefajstos.adapters.copilot_agent_adapter", level="ERROR"):
            self.session.emit(object())


class TestCopilotAgentAdapterPermissions(CopilotAgentAdapterTestCase):
    async def start_turn_and_ask(self, request=None) -> tuple[Any, asyncio.Task]:
        """Start a turn, then let the SDK ask for permission in the middle of it."""
        await self.adapter.start()
        stream = self.adapter.send_and_stream("do something")
        asking = self.ask_for_permission(request)
        return stream, asking

    async def test_the_request_reaches_the_turn_before_the_answer_is_known(
        self,
    ) -> None:
        stream, asking = await self.start_turn_and_ask()

        permission = await self.next_event(stream)

        self.assertIsInstance(permission, PermissionRequested)
        self.assertEqual("config.yaml", permission.summary)
        self.assertFalse(asking.done())

        self.adapter.answer_permission(
            permission.request_id, PermissionDecision.APPROVE_ONCE
        )
        self.assertIsInstance(await asking, PermissionDecisionApproveOnce)

    async def test_the_users_rejection_becomes_an_sdk_rejection(self) -> None:
        stream, asking = await self.start_turn_and_ask()
        permission = await self.next_event(stream)

        self.adapter.answer_permission(permission.request_id, PermissionDecision.REJECT)

        decision = await asking
        self.assertIsInstance(decision, PermissionDecisionReject)
        self.assertEqual(REJECTED_BY_USER_FEEDBACK, decision.feedback)

    async def test_every_request_gets_its_own_id(self) -> None:
        stream, _ = await self.start_turn_and_ask()
        self.ask_for_permission()

        first = await self.next_event(stream)
        second = await self.next_event(stream)

        self.assertNotEqual(first.request_id, second.request_id)
        await self.adapter.abort()

    async def test_answering_an_unknown_request_reports_failure(self) -> None:
        await self.adapter.start()

        with self.assertLogs(
            "hefajstos.adapters.copilot_agent_adapter", level="WARNING"
        ):
            answered = self.adapter.answer_permission(
                "no-such-request", PermissionDecision.REJECT
            )

        self.assertFalse(answered)

    async def test_answering_twice_is_reported_as_failure(self) -> None:
        stream, asking = await self.start_turn_and_ask()
        permission = await self.next_event(stream)
        self.adapter.answer_permission(
            permission.request_id, PermissionDecision.APPROVE_ONCE
        )
        await asking

        with self.assertLogs(
            "hefajstos.adapters.copilot_agent_adapter", level="WARNING"
        ):
            answered = self.adapter.answer_permission(
                permission.request_id, PermissionDecision.REJECT
            )

        self.assertFalse(answered)

    async def test_a_request_nobody_answers_times_out_instead_of_hanging(self) -> None:
        self.adapter.permission_timeout_seconds = 0.01  # type: ignore[assignment]
        await self.adapter.start()

        with self.assertLogs(
            "hefajstos.adapters.copilot_agent_adapter", level="WARNING"
        ):
            decision = await self.ask_for_permission()

        self.assertIsInstance(decision, PermissionDecisionUserNotAvailable)

    async def test_abort_rejects_the_open_request_before_aborting(self) -> None:
        stream, asking = await self.start_turn_and_ask()
        await self.next_event(stream)

        await self.adapter.abort()

        self.assertIsInstance(await asking, PermissionDecisionReject)
        self.assertEqual(["abort"], self.session.calls)

    async def test_stop_answers_the_open_request_before_closing(self) -> None:
        stream, asking = await self.start_turn_and_ask()
        await self.next_event(stream)

        await self.adapter.stop()

        self.assertIsInstance(await asking, PermissionDecisionUserNotAvailable)


class TestCopilotAgentAdapterShutdown(CopilotAgentAdapterTestCase):
    async def test_aborts_unsubscribes_disconnects_and_stops(self) -> None:
        await self.adapter.start()

        await self.adapter.stop()

        self.assertTrue(self.session.unsubscribed)
        self.assertEqual(["abort", "disconnect"], self.session.calls)
        self.assertTrue(self.client.stopped)

    async def test_stops_the_client_even_when_disconnecting_fails(self) -> None:
        await self.adapter.start()

        async def failing_disconnect() -> None:
            raise RuntimeError("disconnect failed")

        self.session.disconnect = failing_disconnect  # type: ignore[method-assign]

        with self.assertLogs("hefajstos.adapters.copilot_agent_adapter", level="ERROR"):
            await self.adapter.stop()

        self.assertTrue(self.client.stopped)

    async def test_aborting_a_session_that_never_started_is_harmless(self) -> None:
        await self.adapter.abort()


class TestToCopilotDecision(unittest.TestCase):
    def test_maps_every_decision_we_can_make(self) -> None:
        expected = {
            PermissionDecision.APPROVE_ONCE: PermissionDecisionApproveOnce,
            PermissionDecision.APPROVE_FOR_SESSION: PermissionDecisionApproveForSession,
            PermissionDecision.REJECT: PermissionDecisionReject,
            PermissionDecision.USER_NOT_AVAILABLE: PermissionDecisionUserNotAvailable,
        }

        for decision in PermissionDecision:
            self.assertIsInstance(_to_copilot_decision(decision), expected[decision])
