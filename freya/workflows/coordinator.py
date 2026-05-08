from __future__ import annotations

from freya.workflows.models import RelationshipType, WorkflowRelationship


class WorkflowCoordinator:
    """In-memory registry of workflow parent-child relationships and delegation contracts.

    Deterministic, local, and inspectable.  All coordination is explicit —
    no peer-to-peer communication, no networking, no distributed execution.
    """

    def __init__(self) -> None:
        self._relationships: list[WorkflowRelationship] = []
        # child_session_id → DelegationContract (stored as dict to avoid circular imports)
        self._contracts: dict[str, object] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, relationship: WorkflowRelationship) -> None:
        """Record a new parent → child relationship."""
        self._relationships.append(relationship)

    def register_contract(self, contract: object) -> None:
        """Store a DelegationContract keyed by child_session_id."""
        child_id = getattr(contract, "child_session_id", None)
        if child_id:
            self._contracts[child_id] = contract

    def spawn_subworkflow(
        self,
        parent_session_id: str,
        child_session_id: str,
        relationship_type: str = RelationshipType.SPAWNED_SUBWORKFLOW,
    ) -> WorkflowRelationship:
        """Create and register a parent → child relationship, returning the model."""
        rel = WorkflowRelationship(
            parent_session_id=parent_session_id,
            child_session_id=child_session_id,
            relationship_type=relationship_type,
        )
        self.register(rel)
        return rel

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_children(self, session_id: str) -> list[str]:
        """Return session IDs of all direct children of *session_id*."""
        return [
            r.child_session_id
            for r in self._relationships
            if r.parent_session_id == session_id
        ]

    def get_parent(self, session_id: str) -> str | None:
        """Return the parent session ID of *session_id*, or None if it is a root."""
        for r in self._relationships:
            if r.child_session_id == session_id:
                return r.parent_session_id
        return None

    def get_contract(self, child_session_id: str) -> object | None:
        """Return the DelegationContract for a given child session, or None."""
        return self._contracts.get(child_session_id)

    def all_contracts(self) -> list[object]:
        """Return all registered delegation contracts."""
        return list(self._contracts.values())

    def workflow_tree(self, session_id: str) -> dict:
        """Return a nested dict representing the workflow subtree rooted at *session_id*."""
        return {
            "session_id": session_id,
            "children": [
                self.workflow_tree(child_id)
                for child_id in self.get_children(session_id)
            ],
        }

    def all_relationships(self) -> list[WorkflowRelationship]:
        """Return a snapshot of all registered relationships."""
        return list(self._relationships)
