"""freya/core.py

Top-level Freya facade.

Three-step API:

    freya = Freya()
    freya.input()   # accept objective from CLI
    freya.plan()    # show domain / phases / agents → Y/n to proceed
    freya.run()     # autonomous execution, generates workspace/<project>/

Methods return self so calls can be chained:
    Freya().input().plan().run()
"""
from __future__ import annotations

import asyncio
import builtins
import logging
from typing import Any

from freya.runtime.runtime import FreyaRuntime, RuntimeResult

logger = logging.getLogger(__name__)

_DIVIDER = "─" * 62

# ---------------------------------------------------------------------------
# Terminal colour helpers — graceful no-op if colorama is absent
# ---------------------------------------------------------------------------
try:
    from colorama import Fore, Style, init as _cinit
    _cinit()
    def _green(s: str)  -> str: return f"{Fore.GREEN}{s}{Style.RESET_ALL}"
    def _red(s: str)    -> str: return f"{Fore.RED}{s}{Style.RESET_ALL}"
    def _cyan(s: str)   -> str: return f"{Fore.CYAN}{s}{Style.RESET_ALL}"
    def _bold(s: str)   -> str: return f"{Style.BRIGHT}{s}{Style.RESET_ALL}"
except ImportError:
    def _green(s: str)  -> str: return s
    def _red(s: str)    -> str: return s
    def _cyan(s: str)   -> str: return s
    def _bold(s: str)   -> str: return s


def _ask(prompt: str) -> bool:
    """Y/n prompt — returns True for yes."""
    try:
        ans = builtins.input(f"{prompt} [Y/n]: ").strip().lower()
    except EOFError:
        return True
    return ans in ("", "y", "yes")


def _render_plan(obj_plan) -> None:
    plan = obj_plan.plan
    print(f"\n{_bold('PLAN')}")
    print(_DIVIDER)
    print(f"  Objective : {plan.objective}")
    print(f"  Domain    : {_cyan(plan.domain)}")
    print(f"\n  {'PHASES':<20} ({len(plan.phases)} total)")
    for i, phase in enumerate(plan.phases, 1):
        agents = ", ".join(phase.required_agent_domains)
        print(f"    {i}.  {_bold(phase.name)}")
        print(f"         {phase.narration}")
        print(f"         agents: [{agents}]")
    print(_DIVIDER)


def _render_result(result: RuntimeResult) -> None:
    wf = result.workflow_result
    status_str = (
        _green("SUCCEEDED")
        if result.succeeded
        else _red(wf.final_status.upper() if wf else "FAILED")
    )
    print(f"\n{_bold('EXECUTION SUMMARY')}")
    print(_DIVIDER)
    print(f"  Status : {status_str}   Domain : {_cyan(result.plan.domain)}")

    completed = set(result.phases_completed)
    print(f"\n  Phases ({len(result.phases_completed)}/{len(result.plan.phases)}):")
    for phase in result.plan.phases:
        sym = _green("✓") if phase.name in completed else _red("✗")
        print(f"    {sym}  {phase.name}")

    # Show generated files if delivery happened
    delivery = (result.final_state or {}).get("delivery", {})
    files_written = delivery.get("files_written", [])
    if files_written:
        import os
        _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print(f"\n  Generated project:")
        for p in files_written:
            print(f"    + {os.path.relpath(p, _root)}")

    wf_errors = wf.errors if wf else []
    if wf_errors:
        print(f"\n  Errors:")
        for e in wf_errors:
            print(f"    {_red('!')}  {e}")

    print(f"\n  Elapsed : {result.metrics.get('elapsed_ms', 0):.0f} ms")
    print(_DIVIDER + "\n")


# ---------------------------------------------------------------------------
# Freya facade
# ---------------------------------------------------------------------------

class Freya:
    """
    Autonomous workflow creation facade.

    Usage:
        freya = Freya()
        freya.input()   # enter objective at CLI
        freya.plan()    # inspect plan, confirm with Y/n
        freya.run()     # Freya executes autonomously and generates output
    """

    def __init__(self) -> None:
        self._runtime     = FreyaRuntime()
        self._objective:  str | None = None
        self._obj_plan    = None
        self._result:     RuntimeResult | None = None

    # ------------------------------------------------------------------
    # Step 1 — Input
    # ------------------------------------------------------------------

    def input(self, prompt: str = "Enter your objective: ") -> "Freya":
        """Accept a free-text objective from the CLI."""
        print(f"\n{_bold('Freya — Autonomous Workflow Creator')}")
        print(_DIVIDER)
        try:
            objective = builtins.input(prompt).strip()
        except EOFError:
            objective = ""
        if not objective:
            raise SystemExit("No objective provided.")
        self._objective = objective
        print(f"\n  Objective received: {_cyan(objective)}")
        return self

    # ------------------------------------------------------------------
    # Step 2 — Plan
    # ------------------------------------------------------------------

    def plan(self) -> "Freya":
        """Generate and display the workflow plan. Confirm to proceed."""
        if not self._objective:
            raise RuntimeError("Call input() before plan().")

        print("\nGenerating plan …")
        self._obj_plan = self._runtime.plan_objective(self._objective)
        _render_plan(self._obj_plan)

        if not _ask("Proceed with this plan?"):
            raise SystemExit("Plan rejected.")

        return self

    # ------------------------------------------------------------------
    # Step 3 — Run
    # ------------------------------------------------------------------

    def run(self) -> RuntimeResult:
        """
        Execute the workflow autonomously. For software objectives Freya
        will generate a workspace/<project>/ folder containing agents/,
        tools/, and policies/.

        Returns:
            RuntimeResult with full execution record.
        """
        if self._obj_plan is None:
            raise RuntimeError("Call plan() before run().")

        print(f"\n{_bold('EXECUTING …')}")
        print(_DIVIDER)

        self._result = asyncio.run(
            self._runtime.execute_objective(self._objective)
        )
        _render_result(self._result)
        return self._result
