from dataclasses import dataclass

from hefajstos.services.models.agent_events import PermissionRequested


@dataclass(slots=True)
class PermissionViewModel:
    request_id: str
    title: str
    summary: str
    detail: str

    @classmethod
    def from_event(cls, request: PermissionRequested) -> "PermissionViewModel":
        return cls(
            request_id=request.request_id,
            title=f"Permission: {request.action}",
            summary=request.summary,
            detail=request.detail,
        )
