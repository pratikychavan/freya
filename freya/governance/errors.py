from __future__ import annotations


class WorkflowVersionConflictError(Exception):
    """Raised when a snapshot save is rejected due to a stale version.

    This indicates that another runner has already written a newer snapshot
    for the same session.  The caller should reload the snapshot and retry
    rather than blindly overwriting the current state.
    """

    def __init__(
        self,
        session_id: str,
        expected_version: int,
        actual_version: int,
    ) -> None:
        self.session_id = session_id
        self.expected_version = expected_version
        self.actual_version = actual_version
        super().__init__(
            f"Snapshot version conflict for session '{session_id}': "
            f"expected version {expected_version}, "
            f"but persisted version is {actual_version}."
        )


class WorkflowLeaseError(Exception):
    """Raised when a runner attempts an operation it does not hold a lease for.

    Examples:
    - resuming a workflow leased by another runner
    - acquiring a lease that is already held and not yet expired
    """

    def __init__(self, session_id: str, reason: str) -> None:
        self.session_id = session_id
        super().__init__(f"Lease error for session '{session_id}': {reason}")


class WorkflowAlreadyResumedError(Exception):
    """Raised when a runner attempts to resume a workflow that has already
    progressed past the PAUSED_FOR_APPROVAL state (e.g. it was already
    resumed by another runner or the same runner calling resume twice).
    """

    def __init__(self, session_id: str, current_state: str) -> None:
        self.session_id = session_id
        self.current_state = current_state
        super().__init__(
            f"Workflow '{session_id}' cannot be resumed: "
            f"current state is '{current_state}' (expected paused_for_approval)."
        )
