from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from freya.dag.models import DAG
from freya.planner.context import PlanningContext


class BasePlanner(ABC):
    """Abstract planner interface.

    Implementations receive a PlanningContext and return the next DAG fragment
    to execute.  Returning a DAG with an empty tasks list signals termination.
    """

    @abstractmethod
    async def plan_next(self, context: PlanningContext) -> DAG:
        """Return the next DAG fragment given the current planning context."""
        ...

    async def repair_dag(
        self,
        context: PlanningContext,
        broken_dag: DAG,
        validation_issues_text: str,
    ) -> DAG:
        """Attempt to repair a rejected DAG fragment.

        The default implementation delegates to plan_next so that planners
        without an explicit repair strategy still behave safely.  Subclasses
        should override this to provide targeted repair prompting.
        """
        return await self.plan_next(context)

    async def plan_recovery(
        self,
        context: PlanningContext,
        failed_observations: list[Any],
    ) -> DAG:
        """Generate a targeted recovery DAG fragment for runtime-failed tasks.

        Receives only the failed observations (not the full context).  The
        default implementation delegates to plan_next so that planners without
        an explicit recovery strategy still behave safely.  Subclasses should
        override this to generate a focused recovery plan.
        """
        return await self.plan_next(context)
