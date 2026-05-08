from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from freya.governance.approval import ApprovalRequest
from freya.governance.errors import (
    WorkflowLeaseError,
    WorkflowVersionConflictError,
)
from freya.governance.snapshot import WorkflowSnapshot
from freya.governance.state import WorkflowState


class PersistentWorkflowStore:
    """File-based persistent store for workflow snapshots and approval requests.

    Layout::

        <base_dir>/
          workflows/<session_id>.json
          approvals/<request_id>.json

    All writes are atomic (write to temp file then rename) so a crash during
    a write never leaves a corrupt file on disk.

    Optimistic concurrency is enforced via ``version``.  Every successful
    ``save_snapshot`` increments the version; a stale write raises
    :class:`~freya.governance.errors.WorkflowVersionConflictError`.

    Workflow leases are embedded inside the snapshot itself and are managed
    via :meth:`acquire_lease` / :meth:`release_lease`.  Only the lease owner
    may perform write operations that require a lease.
    """

    def __init__(self, base_dir: str | Path = ".freya_state") -> None:
        self._base = Path(base_dir)
        self._workflows_dir = self._base / "workflows"
        self._approvals_dir = self._base / "approvals"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        """Write *content* to *path* atomically via temp-file rename."""
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path_str = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(content)
            os.replace(tmp_path_str, str(path))
        except Exception:
            try:
                os.unlink(tmp_path_str)
            except OSError:
                pass
            raise

    def _load_raw_snapshot(self, session_id: str) -> WorkflowSnapshot | None:
        path = self._workflows_dir / f"{session_id}.json"
        if not path.exists():
            return None
        return WorkflowSnapshot.model_validate(
            json.loads(path.read_text(encoding="utf-8"))
        )

    # ------------------------------------------------------------------
    # Snapshot operations
    # ------------------------------------------------------------------

    def save_snapshot(
        self,
        snapshot: WorkflowSnapshot,
        expected_version: int | None = None,
    ) -> Path:
        """Persist *snapshot* to disk with optimistic concurrency control.

        Parameters
        ----------
        snapshot:
            The snapshot to persist.  Its ``version`` field will be
            incremented by this method before writing.
        expected_version:
            If not ``None``, the currently-persisted snapshot's version must
            equal this value.  A mismatch raises
            :class:`~freya.governance.errors.WorkflowVersionConflictError`.

        Returns
        -------
        Path
            The file path that was written.
        """
        path = self._workflows_dir / f"{snapshot.session_id}.json"

        if expected_version is not None:
            current = self._load_raw_snapshot(snapshot.session_id)
            current_version = current.version if current is not None else 0
            if current_version != expected_version:
                raise WorkflowVersionConflictError(
                    session_id=snapshot.session_id,
                    expected_version=expected_version,
                    actual_version=current_version,
                )

        # Increment version and stamp updated_at.
        snapshot = snapshot.model_copy(
            update={
                "version": snapshot.version + 1,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        self._atomic_write(path, json.dumps(snapshot.model_dump(mode="json"), indent=2))
        return path

    def load_snapshot(self, session_id: str) -> WorkflowSnapshot | None:
        """Load and return the snapshot for *session_id*, or ``None`` if absent."""
        return self._load_raw_snapshot(session_id)

    def delete_snapshot(self, session_id: str) -> None:
        """Delete the snapshot file for *session_id* (no-op if absent)."""
        path = self._workflows_dir / f"{session_id}.json"
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    # ------------------------------------------------------------------
    # Lease operations
    # ------------------------------------------------------------------

    def acquire_lease(
        self,
        session_id: str,
        owner_id: str,
        ttl_seconds: int = 30,
    ) -> WorkflowSnapshot:
        """Claim an exclusive execution lease on *session_id*.

        If no snapshot exists a :class:`RuntimeError` is raised.  If a live
        (non-expired) lease is already held by a *different* owner a
        :class:`~freya.governance.errors.WorkflowLeaseError` is raised.

        Returns the updated snapshot (with ``lease_owner`` and
        ``lease_expires_at`` set).
        """
        snapshot = self._load_raw_snapshot(session_id)
        if snapshot is None:
            raise RuntimeError(f"No snapshot found for session '{session_id}'.")

        now = datetime.now(timezone.utc)

        # A lease with no expiry is held permanently until explicitly released.
        # A lease with an expiry blocks only while not yet elapsed.
        lease_active = (
            snapshot.lease_owner is not None
            and snapshot.lease_owner != owner_id
            and (
                snapshot.lease_expires_at is None  # permanent hold
                or snapshot.lease_expires_at > now  # TTL not yet elapsed
            )
        )
        if lease_active:
            raise WorkflowLeaseError(
                session_id,
                f"Lease is held by '{snapshot.lease_owner}' "
                + (
                    "(no expiry — permanent until released)."
                    if snapshot.lease_expires_at is None
                    else f"until {snapshot.lease_expires_at.isoformat()}."
                ),
            )

        updated = snapshot.model_copy(
            update={
                "lease_owner": owner_id,
                "lease_expires_at": now + timedelta(seconds=ttl_seconds),
            }
        )
        # Save without version check — lease acquisition always forces a write.
        self._atomic_write(
            self._workflows_dir / f"{session_id}.json",
            json.dumps(updated.model_dump(mode="json"), indent=2),
        )
        return updated

    def release_lease(self, session_id: str, owner_id: str) -> WorkflowSnapshot:
        """Release an execution lease previously held by *owner_id*.

        No-op if the snapshot has no lease or the lease belongs to a different
        owner (expired reclaim scenario).  Returns the updated snapshot.
        """
        snapshot = self._load_raw_snapshot(session_id)
        if snapshot is None:
            raise RuntimeError(f"No snapshot found for session '{session_id}'.")

        if snapshot.lease_owner != owner_id:
            # Nothing to release — either already expired or held by another.
            return snapshot

        updated = snapshot.model_copy(
            update={"lease_owner": None, "lease_expires_at": None}
        )
        self._atomic_write(
            self._workflows_dir / f"{session_id}.json",
            json.dumps(updated.model_dump(mode="json"), indent=2),
        )
        return updated

    def has_valid_lease(self, session_id: str, owner_id: str) -> bool:
        """Return ``True`` if *owner_id* currently holds a valid (non-expired) lease."""
        snapshot = self._load_raw_snapshot(session_id)
        if snapshot is None:
            return False
        if snapshot.lease_owner != owner_id:
            return False
        # lease_expires_at=None means permanent hold — still valid.
        if snapshot.lease_expires_at is None:
            return True
        return snapshot.lease_expires_at > datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Approval request operations
    # ------------------------------------------------------------------

    def save_approval(self, request: ApprovalRequest) -> Path:
        """Persist *request* to disk.  Returns the file path written."""
        path = self._approvals_dir / f"{request.request_id}.json"
        self._atomic_write(path, json.dumps(request.model_dump(mode="json"), indent=2))
        return path

    def load_approval(self, request_id: str) -> ApprovalRequest | None:
        """Load and return the approval request, or ``None`` if absent."""
        path = self._approvals_dir / f"{request_id}.json"
        if not path.exists():
            return None
        return ApprovalRequest.model_validate(
            json.loads(path.read_text(encoding="utf-8"))
        )

    def approve_approval(self, request_id: str) -> None:
        """Approve a persisted request (load → mutate state → save)."""
        req = self.load_approval(request_id)
        if req is None:
            raise KeyError(f"ApprovalRequest '{request_id}' not found on disk.")
        req.state = WorkflowState.APPROVED
        self.save_approval(req)

    def reject_approval(self, request_id: str) -> None:
        """Reject a persisted request (load → mutate state → save)."""
        req = self.load_approval(request_id)
        if req is None:
            raise KeyError(f"ApprovalRequest '{request_id}' not found on disk.")
        req.state = WorkflowState.REJECTED
        self.save_approval(req)

    def pending_approvals(self) -> list[ApprovalRequest]:
        """Return all persisted requests still in PAUSED_FOR_APPROVAL state."""
        if not self._approvals_dir.exists():
            return []
        result: list[ApprovalRequest] = []
        for path in sorted(self._approvals_dir.glob("*.json")):
            try:
                req = ApprovalRequest.model_validate(
                    json.loads(path.read_text(encoding="utf-8"))
                )
                if req.state == WorkflowState.PAUSED_FOR_APPROVAL:
                    result.append(req)
            except Exception:
                continue
        return result
