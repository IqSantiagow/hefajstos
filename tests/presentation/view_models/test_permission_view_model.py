import unittest

from hefajstos.presentation.view_models.permission_view_model import PermissionViewModel
from hefajstos.services.models.agent_events import PermissionRequested


def make_permission(**overrides) -> PermissionRequested:
    defaults = dict(
        request_id="req-1",
        action="run command",
        summary="rm -rf build",
        detail="Clean the build directory",
        requires_manual_approval=False,
    )
    defaults.update(overrides)
    return PermissionRequested(**defaults)  # type: ignore[arg-type]


class TestPermissionViewModel(unittest.TestCase):
    def test_puts_the_action_in_the_title(self) -> None:
        view_model = PermissionViewModel.from_event(make_permission())

        self.assertEqual("Permission: run command", view_model.title)

    def test_keeps_the_summary_and_the_detail(self) -> None:
        view_model = PermissionViewModel.from_event(make_permission())

        self.assertEqual("rm -rf build", view_model.summary)
        self.assertEqual("Clean the build directory", view_model.detail)

    def test_carries_the_request_id_so_the_answer_finds_its_way_back(self) -> None:
        view_model = PermissionViewModel.from_event(
            make_permission(request_id="req-42")
        )

        self.assertEqual("req-42", view_model.request_id)
