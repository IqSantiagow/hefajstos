from textual.reactive import reactive

from hefajstos.services.models.agent_events import AgentStatus
from hefajstos.ui.widgets.widget_spinner import WidgetSpinner

WORKING_TEXT = "Working… (ctrl+x to abort)"


class WidgetWorkingIndicator(WidgetSpinner):
    agent_status: reactive[AgentStatus] = reactive(AgentStatus.STARTING)

    def watch_agent_status(self, new_status: AgentStatus) -> None:
        if new_status == AgentStatus.THINKING:
            self.start(WORKING_TEXT)
        else:
            self.stop()
