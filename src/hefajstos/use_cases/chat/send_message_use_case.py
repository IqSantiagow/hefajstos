from hefajstos.protocols.agent_protocol import AgentProtocol


class SendMessageUseCase:
    def __init__(self, agent_protocol: AgentProtocol) -> None:
        self.agent_protocol = agent_protocol

    def __call__(self, prompt: str) -> None:
        self.agent_protocol.add_prompt_to_queue(prompt)
