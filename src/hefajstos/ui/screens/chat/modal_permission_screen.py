from textual import on
from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

from hefajstos.presentation.view_models.permission_view_model import PermissionViewModel
from hefajstos.services.models.agent_events import PermissionDecision

APPROVE_BUTTON_ID = "permission-approve"
REJECT_BUTTON_ID = "permission-reject"


class ModalPermissionScreen(ModalScreen[PermissionDecision]):
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
            yield Label(self.view_model.title, classes="permission-title")
            yield Static(
                self.view_model.summary, markup=False, classes="permission-summary"
            )
            yield Static(
                self.view_model.detail, markup=False, classes="permission-detail"
            )
            with HorizontalGroup(classes="permission-buttons"):
                yield Button("Allow  (y)", id=APPROVE_BUTTON_ID, variant="success")
                yield Button("Reject  (n)", id=REJECT_BUTTON_ID, variant="error")

    def on_mount(self) -> None:
        self.query_one(f"#{APPROVE_BUTTON_ID}", Button).focus()

    @on(Button.Pressed, f"#{APPROVE_BUTTON_ID}")
    def handle_approve_pressed(self) -> None:
        self.action_approve()

    @on(Button.Pressed, f"#{REJECT_BUTTON_ID}")
    def handle_reject_pressed(self) -> None:
        self.action_reject()

    def action_approve(self) -> None:
        self.dismiss(PermissionDecision.APPROVE_ONCE)

    def action_reject(self) -> None:
        self.dismiss(PermissionDecision.REJECT)
