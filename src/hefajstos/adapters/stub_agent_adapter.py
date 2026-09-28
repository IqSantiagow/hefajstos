"""A scripted agent that never talks to GitHub. AGENT__ENGINE=stub turns it on."""

import asyncio
from collections.abc import AsyncGenerator

from hefajstos.services.models.agent_events import (
    AgentEvent,
    AgentText,
    PermissionDecision,
    PermissionRequested,
    TokensUsed,
    ToolFinished,
    ToolStarted,
)

# Slow enough to see the streaming, fast enough not to be annoying.
WORD_DELAY_SECONDS = 0.04

OPENING_WORDS = "Sure, I will start by checking what is in the directory.\n".split(" ")

CLOSING_WORDS = (
    "I see one file. This answer comes from the stub - the real agent sits"
    " behind the same interface."
).split(" ")


class StubAgentAdapter:
    def __init__(self, model: str, working_directory: str) -> None:
        self.model = model
        self.working_directory = working_directory
        self.__turn_number = 0
        self.__was_aborted = False
        self.__permission_id = ""
        self.__permission_answer: asyncio.Future | None = None

    async def start(self) -> None:
        pass

    async def send_and_stream(self, prompt: str) -> AsyncGenerator[AgentEvent, None]:
        self.__turn_number += 1
        self.__was_aborted = False

        async for event in self.__stream_words("opening", OPENING_WORDS):
            yield event
        if self.__was_aborted:
            return

        self.__permission_id = f"stub-permission-{self.__turn_number}"
        self.__permission_answer = asyncio.get_running_loop().create_future()
        yield PermissionRequested(
            request_id=self.__permission_id,
            action="run command",
            summary="ls",
            detail="Check what is in the working directory.",
            requires_manual_approval=False,
        )
        decision = await self.__permission_answer
        if self.__was_aborted:
            return

        # A rejected tool does not run, so it reports nothing.
        if decision is PermissionDecision.APPROVE_ONCE:
            tool_call_id = f"stub-call-{self.__turn_number}"
            yield ToolStarted(
                tool_call_id=tool_call_id,
                tool_name="execute",
                arguments={"command": "ls"},
            )
            await asyncio.sleep(WORD_DELAY_SECONDS * 5)
            yield ToolFinished(
                tool_call_id=tool_call_id, success=True, content="README.md"
            )

        async for event in self.__stream_words("closing", CLOSING_WORDS):
            yield event

        yield TokensUsed(input_tokens=1200, output_tokens=180)

    def answer_permission(self, request_id: str, decision: PermissionDecision) -> bool:
        if request_id != self.__permission_id:
            return False
        if self.__permission_answer is None or self.__permission_answer.done():
            return False
        self.__permission_answer.set_result(decision)
        return True

    async def abort(self) -> None:
        self.__was_aborted = True
        self.answer_permission(self.__permission_id, PermissionDecision.REJECT)

    async def stop(self) -> None:
        self.__was_aborted = True
        self.answer_permission(
            self.__permission_id, PermissionDecision.USER_NOT_AVAILABLE
        )

    async def __stream_words(
        self, name: str, words: list[str]
    ) -> AsyncGenerator[AgentText, None]:
        message_id = f"stub-{name}-{self.__turn_number}"
        for word in words:
            if self.__was_aborted:
                return
            yield AgentText(message_id=message_id, text=word + " ", is_final=False)
            await asyncio.sleep(WORD_DELAY_SECONDS)
        yield AgentText(message_id=message_id, text=" ".join(words), is_final=True)
