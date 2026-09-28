from hefajstos.protocols.agent_protocol import AgentProtocol
from hefajstos.services.models.agent_events import PermissionDecision


class AnswerPermissionUseCase:
    def __init__(self, agent_protocol: AgentProtocol) -> None:
        self.agent_protocol = agent_protocol

    def __call__(self, request_id: str, decision: PermissionDecision) -> bool:
        return self.agent_protocol.answer_permission(request_id, decision)
