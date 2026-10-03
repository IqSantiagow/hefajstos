import unittest
from collections.abc import AsyncGenerator

from hefajstos.presentation.chat_repository import ChatRepository
from hefajstos.services.models.agent_events import PermissionDecision
from hefajstos.services.models.model_choice import ModelSelection


class FakeCallUseCase:
    def __init__(self, answer=None) -> None:
        self.answer = answer
        self.calls: list[tuple] = []

    def __call__(self, *args):
        self.calls.append(args)
        return self.answer


class FakeAwaitableUseCase:
    def __init__(self, answer=None) -> None:
        self.answer = answer
        self.calls = 0

    async def __call__(self):
        self.calls += 1
        return self.answer


class FakeAsyncCallUseCase:
    def __init__(self, answer=None) -> None:
        self.answer = answer
        self.calls: list[tuple] = []

    async def __call__(self, *args):
        self.calls.append(args)
        return self.answer


class FakeStreamUseCase:
    def __init__(self, items: list) -> None:
        self.items = items

    async def __call__(self) -> AsyncGenerator:
        for item in self.items:
            yield item


def make_repository(**overrides) -> ChatRepository:
    defaults = dict(
        start_agent_use_case=None,
        shutdown_agent_use_case=None,
        stream_agent_responses_use_case=None,
        send_message_use_case=None,
        answer_permission_use_case=None,
        abort_turn_use_case=None,
        list_commands_use_case=None,
        run_command_use_case=None,
        change_model_use_case=None,
    )
    defaults.update(overrides)
    return ChatRepository(**defaults)  # type: ignore[arg-type]


class TestChatRepositoryLifecycle(unittest.IsolatedAsyncioTestCase):
    async def test_start_agent_returns_what_its_use_case_returns(self) -> None:
        use_case = FakeAwaitableUseCase(answer="agent info")

        agent_info = await make_repository(start_agent_use_case=use_case).start_agent()

        self.assertEqual("agent info", agent_info)

    async def test_shutdown_agent_calls_its_use_case(self) -> None:
        use_case = FakeAwaitableUseCase()

        await make_repository(shutdown_agent_use_case=use_case).shutdown_agent()

        self.assertEqual(1, use_case.calls)

    async def test_abort_turn_calls_its_use_case(self) -> None:
        use_case = FakeAwaitableUseCase()

        await make_repository(abort_turn_use_case=use_case).abort_turn()

        self.assertEqual(1, use_case.calls)


class TestChatRepositoryStream(unittest.IsolatedAsyncioTestCase):
    async def test_agent_responses_come_straight_from_the_use_case(self) -> None:
        repository = make_repository(
            stream_agent_responses_use_case=FakeStreamUseCase(["a", "b"])
        )

        items = [item async for item in repository.stream_agent_responses()]

        self.assertEqual(["a", "b"], items)


class TestChatRepositoryCommands(unittest.TestCase):
    def test_send_message_passes_the_prompt_through(self) -> None:
        use_case = FakeCallUseCase()

        make_repository(send_message_use_case=use_case).send_message("do something")

        self.assertEqual([("do something",)], use_case.calls)

    def test_answer_permission_passes_both_arguments_and_returns_the_answer(
        self,
    ) -> None:
        use_case = FakeCallUseCase(answer=True)

        answered = make_repository(
            answer_permission_use_case=use_case
        ).answer_permission("req-1", PermissionDecision.APPROVE_ONCE)

        self.assertTrue(answered)
        self.assertEqual([("req-1", PermissionDecision.APPROVE_ONCE)], use_case.calls)


class TestChatRepositorySlashCommands(unittest.IsolatedAsyncioTestCase):
    def test_list_commands_passes_the_prefix_and_returns_the_rows(self) -> None:
        use_case = FakeCallUseCase(answer=["row"])

        rows = make_repository(list_commands_use_case=use_case).list_commands("/mo")

        self.assertEqual(["row"], rows)
        self.assertEqual([("/mo",)], use_case.calls)

    async def test_run_command_passes_the_text_and_returns_the_outcome(self) -> None:
        use_case = FakeAsyncCallUseCase(answer="outcome")

        outcome = await make_repository(run_command_use_case=use_case).run_command(
            "/clear"
        )

        self.assertEqual("outcome", outcome)
        self.assertEqual([("/clear",)], use_case.calls)

    async def test_change_model_passes_the_selection_through(self) -> None:
        use_case = FakeAsyncCallUseCase(answer="changed")
        selection = ModelSelection(model_id="gpt-5", settings={})

        result = await make_repository(change_model_use_case=use_case).change_model(
            selection
        )

        self.assertEqual("changed", result)
        self.assertEqual([(selection,)], use_case.calls)
