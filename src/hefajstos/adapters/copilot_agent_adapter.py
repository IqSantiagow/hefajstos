import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import Any
from uuid import uuid4

from copilot import CopilotClient, SessionEvent
from copilot.rpc import (
    PermissionDecisionApproveForSession,
    PermissionDecisionApproveOnce,
    PermissionDecisionReject,
    PermissionDecisionUserNotAvailable,
)

from hefajstos.adapters.copilot_event_mapper import (
    map_permission_request,
    map_session_event,
)
from hefajstos.services.models.agent_events import (
    AgentError,
    AgentEvent,
    PermissionDecision,
    TurnFinished,
)

logger = logging.getLogger(__name__)

REJECTED_BY_USER_FEEDBACK = "Rejected by the user."


class CopilotAgentAdapter:
    def __init__(
        self,
        model: str,
        working_directory: str,
        permission_timeout_seconds: int,
    ) -> None:
        self.model = model
        self.working_directory = working_directory
        self.permission_timeout_seconds = permission_timeout_seconds
        self.__client: CopilotClient | None = None
        self.__session: Any = None
        self.__unsubscribe: Any = None
        self.__loop: asyncio.AbstractEventLoop | None = None
        self.__event_queue: asyncio.Queue[AgentEvent] = asyncio.Queue()
        self.__pending_permissions: dict[str, asyncio.Future] = {}

    async def start(self) -> None:
        self.__loop = asyncio.get_running_loop()
        self.__client = CopilotClient(working_directory=self.working_directory)
        await self.__client.start()
        await self.__check_model_exists()
        self.__session = await self.__client.create_session(
            model=self.model,
            working_directory=self.working_directory,
            streaming=True,
            on_permission_request=self.__on_permission_request,
        )
        self.__unsubscribe = self.__session.on(self.__on_sdk_event)

    async def send_and_stream(self, prompt: str) -> AsyncGenerator[AgentEvent, None]:
        if self.__session is None:
            raise RuntimeError("The session is not started. Call start() first.")

        # Leftovers from before this prompt must not end it early.
        while not self.__event_queue.empty():
            self.__event_queue.get_nowait()

        await self.__session.send(prompt)

        while True:
            event = await self.__event_queue.get()
            if isinstance(event, TurnFinished):
                return
            yield event
            # The SDK's own send_and_wait also stops on an error.
            if isinstance(event, AgentError):
                return

    def answer_permission(self, request_id: str, decision: PermissionDecision) -> bool:
        future = self.__pending_permissions.get(request_id)
        if future is None or future.done():
            logger.warning("No pending permission request %s to answer", request_id)
            return False
        future.set_result(decision)
        return True

    async def abort(self) -> None:
        # The agent waits for these answers, so without this abort would wait too.
        self.__answer_all_pending_permissions(PermissionDecision.REJECT)
        if self.__session is None:
            return
        await self.__session.abort()

    async def stop(self) -> None:
        """Order matters: open permissions first, or the CLI process hangs."""
        self.__answer_all_pending_permissions(PermissionDecision.USER_NOT_AVAILABLE)

        if self.__session is not None:
            try:
                await self.__session.abort()
            except Exception as e:
                logger.exception("Failed to abort the turn", exc_info=e)

        if self.__unsubscribe is not None:
            try:
                self.__unsubscribe()
            except Exception as e:
                logger.exception("Failed to unsubscribe from the session", exc_info=e)
            self.__unsubscribe = None

        if self.__session is not None:
            try:
                await self.__session.disconnect()
            except Exception as e:
                logger.exception("Failed to disconnect the session", exc_info=e)
            self.__session = None

        if self.__client is not None:
            try:
                await self.__client.stop()
            except Exception as e:
                logger.exception("Failed to stop the Copilot client", exc_info=e)
            self.__client = None

    async def __check_model_exists(self) -> None:
        """A stale model name in .env is the most likely reason the app won't start."""
        if self.__client is None:
            return
        try:
            available = [model.id for model in await self.__client.list_models()]
        except Exception as e:
            logger.warning("Could not list models, skipping the check", exc_info=e)
            return
        if self.model in available:
            return
        raise ValueError(
            f"Model {self.model!r} does not exist. Available: {', '.join(available)}"
        )

    def __on_sdk_event(self, event: SessionEvent) -> None:
        # Called by the SDK, so nothing here may raise.
        try:
            mapped = map_session_event(event)
            if mapped is not None:
                self.__put_on_event_queue(mapped)
        except Exception as e:
            logger.exception("Failed to handle a session event", exc_info=e)

    async def __on_permission_request(self, request: Any, invocation: Any) -> Any:
        """The agent is stopped until this returns - the return value is the answer.

        The SDK does not tell us its request id, so we make our own.
        """
        permission = map_permission_request(request, uuid4().hex)
        future = asyncio.get_running_loop().create_future()
        self.__pending_permissions[permission.request_id] = future
        self.__put_on_event_queue(permission)

        try:
            decision = await asyncio.wait_for(
                future, timeout=self.permission_timeout_seconds
            )
        except (asyncio.TimeoutError, asyncio.CancelledError):
            logger.warning("Permission request %s got no answer", permission.request_id)
            decision = PermissionDecision.USER_NOT_AVAILABLE
        finally:
            self.__pending_permissions.pop(permission.request_id, None)

        return _to_copilot_decision(decision)

    def __put_on_event_queue(self, event: AgentEvent) -> None:
        # Always through call_soon_threadsafe: it keeps the order of events even
        # if the SDK calls us from its own thread. Never mix it with put_nowait.
        if self.__loop is None:
            return
        try:
            self.__loop.call_soon_threadsafe(self.__event_queue.put_nowait, event)
        except RuntimeError:
            logger.debug("Event arrived after the loop was closed; dropping it.")

    def __answer_all_pending_permissions(self, decision: PermissionDecision) -> None:
        for future in self.__pending_permissions.values():
            if not future.done():
                future.set_result(decision)


def _to_copilot_decision(decision: PermissionDecision) -> Any:
    if decision is PermissionDecision.APPROVE_ONCE:
        return PermissionDecisionApproveOnce(approved_interactively=True)
    if decision is PermissionDecision.APPROVE_FOR_SESSION:
        return PermissionDecisionApproveForSession(approval=None, domain=None)
    if decision is PermissionDecision.REJECT:
        return PermissionDecisionReject(feedback=REJECTED_BY_USER_FEEDBACK)
    return PermissionDecisionUserNotAvailable()
