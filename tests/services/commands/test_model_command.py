import unittest

from hefajstos.services.commands.model_command import ModelCommand
from hefajstos.services.models.commands import CommandSource, OpenModelPicker
from hefajstos.services.models.model_choice import (
    ModelChoice,
    ModelSelection,
)


class FakeAgent:
    """The part of AgentProtocol that /model reads."""

    def __init__(self) -> None:
        self.model = "gpt-5"
        self.model_settings = {"reasoning_effort": "high"}
        self.working_directory = "/opt/project"
        self.models = [
            ModelChoice(
                id="gpt-5", name="GPT-5", context_window_tokens=None, settings=[]
            )
        ]

    async def list_models(self) -> list[ModelChoice]:
        return self.models

    async def set_model(self, selection: ModelSelection) -> None:
        raise AssertionError("/model only opens the picker")


class TestModelCommand(unittest.IsolatedAsyncioTestCase):
    async def test_opens_the_picker_on_the_current_model(self) -> None:
        agent = FakeAgent()

        result = await ModelCommand(agent_protocol=agent).run("")  # type: ignore[arg-type]

        self.assertEqual(
            OpenModelPicker(
                models=agent.models,
                current_model_id="gpt-5",
                current_settings={"reasoning_effort": "high"},
            ),
            result,
        )

    async def test_the_picker_gets_a_copy_of_the_settings(self) -> None:
        """The picker must not change what the agent holds."""
        agent = FakeAgent()

        result = await ModelCommand(agent_protocol=agent).run("")  # type: ignore[arg-type]

        assert isinstance(result, OpenModelPicker)
        self.assertIsNot(agent.model_settings, result.current_settings)

    def test_is_a_built_in_command_called_model(self) -> None:
        command = ModelCommand(agent_protocol=FakeAgent())  # type: ignore[arg-type]

        self.assertEqual("model", command.name)
        self.assertEqual(CommandSource.BUILT_IN, command.source)
