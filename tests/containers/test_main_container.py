import unittest

from hefajstos.adapters.copilot_agent_adapter import CopilotAgentAdapter
from hefajstos.adapters.stub_agent_adapter import StubAgentAdapter
from hefajstos.config.config import AppConfig
from hefajstos.containers.main_container import Container
from hefajstos.presentation.chat_repository import ChatRepository
from hefajstos.services.agent_service import AgentService


def make_container(**agent_overrides) -> Container:
    container = Container()
    container.config.from_pydantic(AppConfig(agent=agent_overrides))  # type: ignore[arg-type]
    return container


class TestContainerWiring(unittest.TestCase):
    def test_the_repository_graph_resolves(self) -> None:
        self.assertIsInstance(make_container().chat_repository(), ChatRepository)

    def test_the_repository_is_shared(self) -> None:
        container = make_container()

        self.assertIs(container.chat_repository(), container.chat_repository())

    def test_use_cases_are_built_fresh_every_time(self) -> None:
        container = make_container()

        self.assertIsNot(
            container.send_message_use_case(), container.send_message_use_case()
        )

    def test_every_use_case_talks_to_the_same_agent(self) -> None:
        container = make_container()

        agents = {
            container.send_message_use_case().agent_protocol,
            container.abort_turn_use_case().agent_protocol,
            container.stream_agent_responses_use_case().agent_protocol,
        }

        self.assertEqual(1, len(agents))


class TestContainerEngineSelection(unittest.TestCase):
    def test_copilot_is_the_default_engine(self) -> None:
        agent_service = make_container().agent_service()

        self.assertIsInstance(agent_service, AgentService)
        self.assertIsInstance(agent_service.agent_sdk, CopilotAgentAdapter)

    def test_the_stub_engine_runs_behind_the_same_service(self) -> None:
        agent_service = make_container(engine="stub").agent_service()

        self.assertIsInstance(agent_service, AgentService)
        self.assertIsInstance(agent_service.agent_sdk, StubAgentAdapter)


class TestContainerSlashCommands(unittest.TestCase):
    def test_model_and_clear_are_registered(self) -> None:
        commands = make_container(engine="stub").commands_service()

        names = [command.name for command in commands.list_matching("/")]

        self.assertEqual(["clear", "model"], names)
