from __future__ import annotations

import logging
from typing import Any

from freya.policy.base import Policy, PolicyResult

logger = logging.getLogger(__name__)


class PolicyManager:
    def __init__(self) -> None:
        self._policies: list[Policy] = []

    def add_policy(self, policy: Policy) -> None:
        self._policies.append(policy)

    def evaluate_input(
        self, task: dict[str, Any], context: dict[str, Any]
    ) -> list[PolicyResult]:
        results: list[PolicyResult] = []
        for policy in self._policies:
            result = policy.check_input(task, context)
            result.policy_name = type(policy).__name__
            results.append(result)
            if result.action == "WARN":
                logger.warning(
                    "[Policy WARN] task=%s policy=%s reason=%s",
                    context.get("task_id"),
                    result.policy_name,
                    result.reason,
                )
            elif result.action == "BLOCK":
                logger.error(
                    "[Policy BLOCK] task=%s policy=%s reason=%s",
                    context.get("task_id"),
                    result.policy_name,
                    result.reason,
                )
                break  # short-circuit on first BLOCK
        return results

    def evaluate_output(
        self, task: dict[str, Any], result: dict[str, Any], context: dict[str, Any]
    ) -> list[PolicyResult]:
        results: list[PolicyResult] = []
        for policy in self._policies:
            pr = policy.check_output(task, result, context)
            pr.policy_name = type(policy).__name__
            results.append(pr)
            if pr.action == "WARN":
                logger.warning(
                    "[Policy WARN output] task=%s policy=%s reason=%s",
                    context.get("task_id"),
                    pr.policy_name,
                    pr.reason,
                )
            elif pr.action == "BLOCK":
                logger.error(
                    "[Policy BLOCK output] task=%s policy=%s reason=%s",
                    context.get("task_id"),
                    pr.policy_name,
                    pr.reason,
                )
                break  # short-circuit on first BLOCK
        return results

    @staticmethod
    def is_blocked(results: list[PolicyResult]) -> bool:
        return any(r.action == "BLOCK" for r in results)
