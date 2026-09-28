from dependency_injector import containers, providers

from hefajstos.adapters.copilot_agent_adapter import CopilotAgentAdapter
from hefajstos.adapters.stub_agent_adapter import StubAgentAdapter
from hefajstos.config.config import AppConfig
from hefajstos.presentation.chat_repository import ChatRepository
from hefajstos.services.agent_service import AgentService
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


class Container(containers.DeclarativeContainer):
    # ----- CONFIG -----
    config = providers.Configuration(pydantic_settings=[AppConfig()])  # type: ignore

    # ----- ADAPTERS -----
    copilot_adapter = providers.Singleton(
        CopilotAgentAdapter,
        model=config.agent.model,
        working_directory=config.agent.working_directory,
        permission_timeout_seconds=config.agent.permission_timeout_seconds,
    )
    stub_adapter = providers.Singleton(
        StubAgentAdapter,
        model=config.agent.model,
        working_directory=config.agent.working_directory,
    )
    # Selector builds only the adapter it picks.
    agent_sdk = providers.Selector(
        config.agent.engine,
        copilot=copilot_adapter,
        stub=stub_adapter,
    )

    # ----- SERVICES -----
    agent_service = providers.Singleton(
        AgentService,
        agent_sdk=agent_sdk,
        auto_approve_tools=config.agent.auto_approve,
    )

    # ----- USE CASES -----
    start_agent_use_case = providers.Factory(
        StartAgentUseCase, agent_protocol=agent_service
    )
    shutdown_agent_use_case = providers.Factory(
        ShutdownAgentUseCase, agent_protocol=agent_service
    )
    stream_agent_responses_use_case = providers.Factory(
        StreamAgentResponsesUseCase, agent_protocol=agent_service
    )
    send_message_use_case = providers.Factory(
        SendMessageUseCase, agent_protocol=agent_service
    )
    answer_permission_use_case = providers.Factory(
        AnswerPermissionUseCase, agent_protocol=agent_service
    )
    abort_turn_use_case = providers.Factory(
        AbortTurnUseCase, agent_protocol=agent_service
    )

    # ----- REPOSITORIES -----
    chat_repository = providers.Singleton(
        ChatRepository,
        start_agent_use_case=start_agent_use_case,
        shutdown_agent_use_case=shutdown_agent_use_case,
        stream_agent_responses_use_case=stream_agent_responses_use_case,
        send_message_use_case=send_message_use_case,
        answer_permission_use_case=answer_permission_use_case,
        abort_turn_use_case=abort_turn_use_case,
    )
