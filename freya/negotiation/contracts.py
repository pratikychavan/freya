"""freya/negotiation/contracts.py

OperationalNegotiationContractEngine

Persists negotiation agreements, tracks status, and guarantees reversibility.
All contracts are bounded, auditable, and expire automatically or on demand.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from freya.negotiation.models import ContractStatus, NegotiationContract

_CONTRACT_TYPE_TERMS: dict[str, dict[str, str]] = {
    "degradation": {
        "scope":       "Reduced operational quality for specified workflow.",
        "constraint":  "Must not violate minimum quality floor.",
        "expiry":      "Auto-reverted when resource pressure normalises.",
    },
    "resource_borrow": {
        "scope":       "Temporary capacity loan between workflows.",
        "constraint":  "Donor retains at least 60 % of their capacity.",
        "expiry":      "Returned when target workflow pressure normalises.",
    },
    "deferral": {
        "scope":       "Background tasks deferred until capacity available.",
        "constraint":  "Deferred tasks resume within the same operational cycle.",
        "expiry":      "Automatically lifted when pressure drops below 0.55.",
    },
    "batching": {
        "scope":       "Governance reviews aggregated into scheduled batches.",
        "constraint":  "No governance requirement may be permanently deferred.",
        "expiry":      "Dissolved when backlog clears below threshold.",
    },
}


class OperationalNegotiationContractEngine:
    """Create, track, and revert operational negotiation contracts."""

    def __init__(self) -> None:
        self._contracts: dict[str, NegotiationContract] = {}

    # ── Contract lifecycle ─────────────────────────────────────────────────────

    def create(
        self,
        workflow_id: str,
        contract_type: str,
        extra_terms: dict[str, str] | None = None,
        expiry_trigger: str = "pressure_normalizes",
    ) -> NegotiationContract:
        base_terms = dict(_CONTRACT_TYPE_TERMS.get(contract_type, {}))
        if extra_terms:
            base_terms.update(extra_terms)

        now = datetime.now(tz=timezone.utc).isoformat()
        contract = NegotiationContract(
            contract_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            contract_type=contract_type,
            terms=base_terms,
            status="pending",
            reversible=True,
            expiry_trigger=expiry_trigger,
            audit_log=[f"[{now}] Contract created (type={contract_type})."],
        )
        self._contracts[contract.contract_id] = contract
        self._transition(contract, "active", "Contract activated.")
        return contract

    def revert(self, contract_id: str) -> NegotiationContract | None:
        contract = self._contracts.get(contract_id)
        if contract is None or contract.status not in ("active", "pending"):
            return contract
        self._transition(contract, "reverted", "Contract reverted by operational recovery.")
        return contract

    def expire(self, contract_id: str) -> NegotiationContract | None:
        contract = self._contracts.get(contract_id)
        if contract is None or contract.status != "active":
            return contract
        self._transition(contract, "expired", "Contract expired per trigger condition.")
        return contract

    # ── Queries ────────────────────────────────────────────────────────────────

    def active_contracts_for(self, workflow_id: str) -> list[NegotiationContract]:
        return [c for c in self._contracts.values()
                if c.workflow_id == workflow_id and c.status == "active"]

    def expire_all_for(self, workflow_id: str) -> list[NegotiationContract]:
        expired = []
        for contract in list(self._contracts.values()):
            if contract.workflow_id == workflow_id and contract.status == "active":
                self._transition(contract, "expired", "Bulk expiry on workflow recovery.")
                expired.append(contract)
        return expired

    def revert_all_for(self, workflow_id: str) -> list[NegotiationContract]:
        reverted = []
        for contract in list(self._contracts.values()):
            if contract.workflow_id == workflow_id and contract.status in ("active", "pending"):
                self._transition(contract, "reverted", "Bulk revert on workflow recovery.")
                reverted.append(contract)
        return reverted

    def all_contracts(self) -> list[NegotiationContract]:
        return list(self._contracts.values())

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {"active": 0, "pending": 0, "expired": 0, "reverted": 0}
        for c in self._contracts.values():
            counts[c.status] = counts.get(c.status, 0) + 1
        return counts

    # ── Private ────────────────────────────────────────────────────────────────

    @staticmethod
    def _transition(contract: NegotiationContract, new_status: ContractStatus, note: str) -> None:
        now = datetime.now(tz=timezone.utc).isoformat()
        contract.status = new_status
        contract.audit_log.append(f"[{now}] {note} (status → {new_status})")
