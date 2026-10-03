import unittest
from pathlib import Path

from hefajstos.config.config import Agent


class TestAgentWorkingDirectory(unittest.TestCase):
    def test_an_empty_value_becomes_the_current_directory(self) -> None:
        self.assertEqual(str(Path.cwd()), Agent().working_directory)

    def test_expands_a_tilde(self) -> None:
        agent = Agent(working_directory="~")

        self.assertEqual(str(Path.home()), agent.working_directory)

    def test_makes_a_relative_path_absolute(self) -> None:
        agent = Agent(working_directory=".")

        self.assertEqual(str(Path.cwd()), agent.working_directory)


class TestAgentDefaults(unittest.TestCase):
    def test_runs_against_copilot_unless_told_otherwise(self) -> None:
        self.assertEqual("copilot", Agent().engine)

    def test_does_not_auto_approve_by_default(self) -> None:
        self.assertFalse(Agent().auto_approve)
