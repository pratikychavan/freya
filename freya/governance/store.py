from __future__ import annotations

from freya.governance.approval import ApprovalRequest
from freya.governance.state import WorkflowState


class InMemoryApprovalStore:
    """In-memory store for ApprovalRequest lifecycle management."""

    def __init__(self) -> None:
        self._requests: dict[str, ApprovalRequest] = {}

    def create(self, request: ApprovalRequest) -> ApprovalRequest:
        self._requests[request.request_id] = request
        return request

    def get(self, request_id: str) -> ApprovalRequest:
        if request_id not in self._requests:
            raise KeyError(f"ApprovalRequest '{request_id}' not found.")
        return self._requests[request_id]

    def approve(self, request_id: str) -> ApprovalRequest:
        req = self.get(request_id)
        req.state = WorkflowState.APPROVED
        return req

    def reject(self, request_id: str) -> ApprovalRequest:
        req = self.get(request_id)
        req.state = WorkflowState.REJECTED
        return req

    def pending(self) -> list[ApprovalRequest]:
        return [
            r for r in self._requests.values()
            if r.state == WorkflowState.PAUSED_FOR_APPROVAL
        ]
