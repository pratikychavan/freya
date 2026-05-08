from __future__ import annotations

from abc import ABC, abstractmethod

from freya.governance.models import GovernanceDecision


class InterventionPolicy(ABC):
    """Abstract base class for all intervention policies.

    Policies MUST:
    - remain deterministic
    - NOT execute tools
    - NOT mutate memory
    - NOT call the planner
    """

    @abstractmethod
    def evaluate(
        self,
        planning_context: object,
        proposed_dag: object,
    ) -> GovernanceDecision:
        ...
