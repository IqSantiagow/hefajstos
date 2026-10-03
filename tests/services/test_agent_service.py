import asyncio
import tempfile
import unittest
from pathlib import Path
from collections.abc import AsyncGenerator

from hefajstos.services.agent_service import AgentService, is_inside
from hefajstos.services.models.agent_events import (
    AgentError,
    AgentEvent,
    AgentStatus,
    AgentText,
    PermissionDecision,
    PermissionRequested,
    TokensUsed,
)
from hefajstos.services.models.model_choice import (
    ModelChoice,
    ModelSelection,
)

READ_TIMEOUT_SECONDS = 1.0


class FakeAgentSdk:
    def __init__(self, events: list[AgentEvent] | None = None) -> None:
        self.model = "gpt-5"
        self.model_settings: dict[str, str] = {}
        self.working_directory = "/tmp/project"
        self.models = [
            ModelChoice(
                id="gpt-5", name="GPT-5", context_window_tokens=None, settings=[]
            )
        ]
        self.events = events or []
        self.sent_prompts: list[str] = []
        self.answers: list[tuple[str, PermissionDecision]] = []
        self.calls: list[str] = []
        self.failure: Exception | None = None

    async def start(self) -> None:
        self.calls.append("start")

    async def send_and_stream(self, prompt: str) -> AsyncGenerator[AgentEvent, None]:
        self.sent_prompts.append(prompt)
        if self.failure is not None:
            raise self.failure
        for event in self.events:
            yield event

    def answer_permission(self, request_id: str, decision: PermissionDecision) -> bool:
        self.answers.append((request_id, decision))
        return True

    async def list_models(self) -> list[ModelChoice]:
        return self.models

    async def set_model(self, selection: ModelSelection) -> None:
        self.model = selection.model_id
        self.model_settings = selection.settings

    async def abort(self) -> None:
        self.calls.append("abort")

    async def stop(self) -> None:
        self.calls.append("stop")


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


async def read_one_turn(service: AgentService, prompt: str = "fix the tests") -> list:
    service.add_prompt_to_queue(prompt)
    stream = service.consume_prompt_queue()
    items = []

    async def read_until_idle() -> None:
        async for item in stream:
            items.append(item)
            if item is AgentStatus.IDLE:
                return

    await asyncio.wait_for(read_until_idle(), timeout=READ_TIMEOUT_SECONDS)
    await stream.aclose()
    return items


class TestAgentServiceTurn(unittest.IsolatedAsyncioTestCase):
    async def test_a_turn_is_wrapped_in_thinking_and_idle(self) -> None:
        text = AgentText(message_id="m1", text="Hello", is_final=True)
        service = AgentService(FakeAgentSdk(events=[text]), auto_approve_tools=False)

        items = await read_one_turn(service)

        self.assertEqual([AgentStatus.THINKING, text, AgentStatus.IDLE], items)

    async def test_the_prompt_reaches_the_sdk(self) -> None:
        sdk = FakeAgentSdk()
        service = AgentService(sdk, auto_approve_tools=False)

        await read_one_turn(service, "fix the tests")

        self.assertEqual(["fix the tests"], sdk.sent_prompts)

    async def test_prompts_are_sent_one_after_another(self) -> None:
        sdk = FakeAgentSdk()
        service = AgentService(sdk, auto_approve_tools=False)
        service.add_prompt_to_queue("first")

        await read_one_turn(service, "second")
        await read_one_turn(service, "third")

        self.assertEqual(["first", "second"], sdk.sent_prompts)

    async def test_a_failed_turn_becomes_an_error_and_still_ends_idle(self) -> None:
        sdk = FakeAgentSdk()
        sdk.failure = RuntimeError("no network")
        service = AgentService(sdk, auto_approve_tools=False)

        with self.assertLogs("hefajstos.services.agent_service", level="ERROR"):
            items = await read_one_turn(service)

        self.assertIsInstance(items[1], AgentError)
        self.assertIn("no network", items[1].message)
        self.assertEqual(AgentStatus.IDLE, items[-1])


class TestAgentServiceAutoApprove(unittest.IsolatedAsyncioTestCase):
    async def test_answers_for_the_user_when_auto_approve_is_on(self) -> None:
        sdk = FakeAgentSdk(events=[make_permission(request_id="req-7")])
        service = AgentService(sdk, auto_approve_tools=True)

        items = await read_one_turn(service)

        self.assertEqual([("req-7", PermissionDecision.APPROVE_ONCE)], sdk.answers)
        self.assertTrue(items[1].auto_approved)

    async def test_leaves_the_request_to_the_user_when_auto_approve_is_off(
        self,
    ) -> None:
        sdk = FakeAgentSdk(events=[make_permission()])
        service = AgentService(sdk, auto_approve_tools=False)

        items = await read_one_turn(service)

        self.assertEqual([], sdk.answers)
        self.assertFalse(items[1].auto_approved)

    async def test_never_auto_approves_what_requires_manual_approval(self) -> None:
        sdk = FakeAgentSdk(events=[make_permission(requires_manual_approval=True)])
        service = AgentService(sdk, auto_approve_tools=True)

        items = await read_one_turn(service)

        self.assertEqual([], sdk.answers)
        self.assertFalse(items[1].auto_approved)


class TestAgentServiceTokens(unittest.IsolatedAsyncioTestCase):
    async def test_tokens_are_summed_over_the_whole_session(self) -> None:
        sdk = FakeAgentSdk(events=[TokensUsed(input_tokens=100, output_tokens=10)])
        service = AgentService(sdk, auto_approve_tools=False)

        await read_one_turn(service)
        items = await read_one_turn(service)

        self.assertEqual(TokensUsed(input_tokens=200, output_tokens=20), items[1])


class TestAgentServicePassThrough(unittest.IsolatedAsyncioTestCase):
    async def test_takes_the_model_and_directory_from_the_sdk(self) -> None:
        service = AgentService(FakeAgentSdk(), auto_approve_tools=False)

        self.assertEqual("gpt-5", service.model)
        self.assertEqual("/tmp/project", service.working_directory)

    async def test_start_abort_and_shutdown_go_to_the_sdk(self) -> None:
        sdk = FakeAgentSdk()
        service = AgentService(sdk, auto_approve_tools=False)

        await service.start()
        await service.abort_turn()
        await service.shutdown()

        self.assertEqual(["start", "abort", "stop"], sdk.calls)

    async def test_passes_the_users_answer_to_the_sdk(self) -> None:
        sdk = FakeAgentSdk()
        service = AgentService(sdk, auto_approve_tools=False)

        service.answer_permission("req-3", PermissionDecision.REJECT)

        self.assertEqual([("req-3", PermissionDecision.REJECT)], sdk.answers)


class TestAgentServiceModels(unittest.IsolatedAsyncioTestCase):
    async def test_lists_the_models_of_the_sdk(self) -> None:
        sdk = FakeAgentSdk()

        models = await AgentService(sdk, auto_approve_tools=False).list_models()

        self.assertEqual(sdk.models, models)

    async def test_the_model_is_current_after_a_switch(self) -> None:
        service = AgentService(FakeAgentSdk(), auto_approve_tools=False)

        await service.set_model(
            ModelSelection(
                model_id="claude-sonnet-5", settings={"reasoning_effort": "high"}
            )
        )

        self.assertEqual("claude-sonnet-5", service.model)
        self.assertEqual({"reasoning_effort": "high"}, service.model_settings)


class TestIsInside(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = str(Path(temporary.name) / "project")

    def test_a_relative_path_counts_from_the_project(self) -> None:
        self.assertTrue(is_inside("src/main.py", self.project))

    def test_the_project_itself_is_inside(self) -> None:
        self.assertTrue(is_inside(self.project, self.project))

    def test_an_absolute_path_inside_the_project_is_inside(self) -> None:
        self.assertTrue(is_inside(str(Path(self.project, "a.txt")), self.project))

    def test_climbing_out_with_dot_dot_is_outside(self) -> None:
        self.assertFalse(is_inside("../secrets.txt", self.project))

    def test_the_home_directory_is_outside(self) -> None:
        self.assertFalse(is_inside("~/.ssh/id_rsa", self.project))

    def test_a_sibling_with_the_same_prefix_is_outside(self) -> None:
        self.assertFalse(is_inside(self.project + "-old/a.txt", self.project))


class TestAgentServiceProjectReads(unittest.IsolatedAsyncioTestCase):
    async def answers_for(self, permission: PermissionRequested) -> list:
        sdk = FakeAgentSdk(events=[permission])
        await read_one_turn(AgentService(sdk, auto_approve_tools=False))
        return sdk.answers

    async def test_a_read_inside_the_project_is_approved(self) -> None:
        answers = await self.answers_for(
            make_permission(is_read_only=True, paths=["src/main.py"])
        )

        self.assertEqual([("req-1", PermissionDecision.APPROVE_ONCE)], answers)

    async def test_a_read_only_command_without_paths_is_approved(self) -> None:
        answers = await self.answers_for(make_permission(is_read_only=True, paths=[]))

        self.assertEqual(1, len(answers))

    async def test_a_read_outside_the_project_waits_for_the_user(self) -> None:
        answers = await self.answers_for(
            make_permission(is_read_only=True, paths=["src", "~/.ssh/id_rsa"])
        )

        self.assertEqual([], answers)

    async def test_a_request_that_writes_waits_for_the_user(self) -> None:
        answers = await self.answers_for(
            make_permission(is_read_only=False, paths=["src/main.py"])
        )

        self.assertEqual([], answers)

    async def test_a_read_that_requires_manual_approval_waits_for_the_user(
        self,
    ) -> None:
        answers = await self.answers_for(
            make_permission(
                is_read_only=True, paths=["src"], requires_manual_approval=True
            )
        )

        self.assertEqual([], answers)
