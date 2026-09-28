from textual.app import ComposeResult
from textual.containers import VerticalGroup
from textual.screen import ModalScreen
from textual.widgets import Label, Static

from hefajstos.presentation.view_models.permission_view_model import PermissionViewModel
from hefajstos.services.models.agent_events import PermissionDecision

KEY_HINT = "y allow · n reject · esc reject"


class ModalPermissionScreen(ModalScreen[PermissionDecision]):
    """A bar across the bottom of the screen, answered with the keyboard only."""

    BINDINGS = [
        ("y", "approve", "Allow"),
        ("n", "reject", "Reject"),
        # The agent waits for an answer, so Escape rejects instead of closing.
        ("escape", "reject", "Reject"),
    ]

    def __init__(self, view_model: PermissionViewModel, **kwargs) -> None:
        super().__init__(**kwargs)
        self.view_model = view_model

    def compose(self) -> ComposeResult:
        with VerticalGroup(id="permission-dialog"):
            yield Label(
                f"Permission: {self.view_model.action}",
                markup=False,
                classes="permission-title",
            )
            yield Static(
                self.view_model.summary, markup=False, classes="permission-summary"
            )
            detail_classes = "permission-detail" if self.view_model.detail else "hidden"
            yield Static(self.view_model.detail, markup=False, classes=detail_classes)
            yield Label(KEY_HINT, classes="permission-hint")

    def action_approve(self) -> None:
        self.dismiss(PermissionDecision.APPROVE_ONCE)

    def action_reject(self) -> None:
        self.dismiss(PermissionDecision.REJECT)
