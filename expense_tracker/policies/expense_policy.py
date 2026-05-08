from __future__ import annotations

from typing import Any

from freya import Policy, PolicyResult


class ExpenseAmountPolicy(Policy):
    """
    Validates expense tool tasks before execution.

    Rules:
      - Each individual expense amount must not exceed max_single_amount.
      - The combined total of all amounts in a compute_total call must not
        exceed max_total_amount.
      - Negative or zero amounts are always blocked.
    """

    policy_name = "ExpenseAmountPolicy"

    def __init__(
        self,
        max_single_amount: float = 500.0,
        max_total_amount: float = 2000.0,
    ) -> None:
        self._max_single = max_single_amount
        self._max_total = max_total_amount

    def check_input(self, task: dict[str, Any], context: dict[str, Any]) -> PolicyResult:
        if task.get("type") != "tool":
            return PolicyResult(action="ALLOW", policy_name=self.policy_name)

        tool_input: dict[str, Any] = task.get("input", {}).get("tool_input", {})
        tool_name: str = task.get("input", {}).get("tool_name", "")

        # --- Validate individual expense entries ---
        if tool_name == "record_expenses":
            for entry in tool_input.get("expenses", []):
                amount = entry.get("amount", 0)
                if amount <= 0:
                    return PolicyResult(
                        action="BLOCK",
                        reason=f"Expense '{entry.get('category')}' has invalid amount {amount}.",
                        policy_name=self.policy_name,
                    )
                if amount > self._max_single:
                    return PolicyResult(
                        action="BLOCK",
                        reason=(
                            f"Expense '{entry.get('category')}' amount ${amount:.2f} exceeds "
                            f"the per-item limit of ${self._max_single:.2f}."
                        ),
                        policy_name=self.policy_name,
                    )

        # --- Validate bulk amount list ---
        if tool_name == "compute_total":
            amounts: list[float] = tool_input.get("amounts", [])
            for amount in amounts:
                if amount <= 0:
                    return PolicyResult(
                        action="BLOCK",
                        reason=f"Amount {amount} is invalid (must be positive).",
                        policy_name=self.policy_name,
                    )
            total = sum(amounts)
            if total > self._max_total:
                return PolicyResult(
                    action="BLOCK",
                    reason=(
                        f"Total ${total:.2f} exceeds the session limit "
                        f"of ${self._max_total:.2f}."
                    ),
                    policy_name=self.policy_name,
                )

        return PolicyResult(action="ALLOW", policy_name=self.policy_name)

    def check_output(
        self, task: dict[str, Any], result: dict[str, Any], context: dict[str, Any]
    ) -> PolicyResult:
        # Warn if the computed total is unusually high but was allowed through.
        if task.get("input", {}).get("tool_name") == "compute_total":
            total = result.get("total", 0)
            warn_threshold = self._max_total * 0.8
            if total > warn_threshold:
                return PolicyResult(
                    action="WARN",
                    reason=(
                        f"Total ${total:.2f} is above 80% of the session limit "
                        f"(${self._max_total:.2f}). Review before approving."
                    ),
                    policy_name=self.policy_name,
                )
        return PolicyResult(action="ALLOW", policy_name=self.policy_name)
