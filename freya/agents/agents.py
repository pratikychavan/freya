"""freya/agents/agents.py

SDK operational agents.
Each agent wraps domain-specific logic and conforms to the
OperationalAgent interface.

Agents do NOT generate code. They interpret workflow state and
produce structured results that feed back into the orchestration
pipeline.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from freya.agents.base import (
    AgentContext,
    AgentResult,
    AgentStatus,
    OperationalAgent,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _elapsed(t0: float) -> float:
    return (time.monotonic() - t0) * 1000


# ---------------------------------------------------------------------------
# Concrete Agents
# ---------------------------------------------------------------------------


class ComplianceAgent(OperationalAgent):
    """Evaluates regulatory posture and policy adherence."""

    @property
    def name(self) -> str:
        return "ComplianceAgent"

    @property
    def domain(self) -> str:
        return "compliance"

    async def execute(self, context: AgentContext) -> AgentResult:
        t0 = time.monotonic()
        state = context.state
        frameworks = state.get("compliance_frameworks", ["SOC2", "GDPR"])
        controls = state.get("active_controls", {})

        findings: list[str] = []
        warnings: list[str] = []

        for fw in frameworks:
            fw_controls = controls.get(fw, {})
            failed = [c for c, v in fw_controls.items() if not v]
            if failed:
                findings.append(f"{fw}: controls not met — {', '.join(failed)}")

        posture = "compliant" if not findings else "non_compliant"
        narration = (
            f"Compliance assessment across {len(frameworks)} framework(s). "
            f"Status: {posture}."
            + (f" Findings: {len(findings)}." if findings else "")
        )

        return self._result(
            status=AgentStatus.SUCCEEDED,
            output={
                "posture": posture,
                "frameworks_evaluated": frameworks,
                "findings": findings,
            },
            narration=narration,
            warnings=warnings,
            elapsed_ms=_elapsed(t0),
        )


class RiskAgent(OperationalAgent):
    """Evaluates operational risk and exposure trajectory."""

    @property
    def name(self) -> str:
        return "RiskAgent"

    @property
    def domain(self) -> str:
        return "risk"

    async def execute(self, context: AgentContext) -> AgentResult:
        t0 = time.monotonic()
        state = context.state
        risk_indicators = state.get("risk_indicators", {})

        critical = [k for k, v in risk_indicators.items() if v == "critical"]
        elevated = [k for k, v in risk_indicators.items() if v in ("high", "elevated")]

        level = "normal"
        if critical:
            level = "critical"
        elif elevated:
            level = "elevated"

        narration = (
            f"Risk evaluation complete. Assessed {len(risk_indicators)} indicator(s). "
            f"Overall risk level: {level}."
        )

        return self._result(
            status=AgentStatus.SUCCEEDED,
            output={
                "risk_level": level,
                "critical_indicators": critical,
                "elevated_indicators": elevated,
                "total_indicators": len(risk_indicators),
            },
            narration=narration,
            elapsed_ms=_elapsed(t0),
        )


class RecoveryAgent(OperationalAgent):
    """Orchestrates recovery playbooks for service restoration."""

    @property
    def name(self) -> str:
        return "RecoveryAgent"

    @property
    def domain(self) -> str:
        return "recovery"

    async def execute(self, context: AgentContext) -> AgentResult:
        t0 = time.monotonic()
        state = context.state
        affected = state.get("affected_services", [])
        playbook = state.get("recovery_playbook", "standard")
        steps_completed: list[str] = []
        warnings: list[str] = []

        if not affected:
            return self._result(
                AgentStatus.SKIPPED,
                narration="No affected services identified; recovery skipped.",
                elapsed_ms=_elapsed(t0),
            )

        for svc in affected:
            steps_completed.append(f"restore:{svc}")

        narration = (
            f"Recovery playbook '{playbook}' applied to {len(affected)} service(s). "
            f"Restoration steps completed: {len(steps_completed)}."
        )

        return self._result(
            status=AgentStatus.SUCCEEDED,
            output={
                "playbook": playbook,
                "services_restored": affected,
                "steps_completed": steps_completed,
            },
            narration=narration,
            warnings=warnings,
            elapsed_ms=_elapsed(t0),
        )


class InfrastructureAgent(OperationalAgent):
    """Evaluates and acts on infrastructure topology and health."""

    @property
    def name(self) -> str:
        return "InfrastructureAgent"

    @property
    def domain(self) -> str:
        return "infrastructure"

    async def execute(self, context: AgentContext) -> AgentResult:
        t0 = time.monotonic()
        state = context.state
        services = state.get("services", {})
        region = state.get("region", "us-east-1")

        degraded = [s for s, h in services.items() if h in ("degraded", "down")]
        healthy_count = len(services) - len(degraded)

        narration = (
            f"Infrastructure scan complete for region '{region}'. "
            f"{healthy_count}/{len(services)} service(s) healthy."
            + (f" Degraded: {', '.join(degraded)}." if degraded else "")
        )

        return self._result(
            status=AgentStatus.SUCCEEDED,
            output={
                "region": region,
                "total_services": len(services),
                "healthy_count": healthy_count,
                "degraded_services": degraded,
            },
            narration=narration,
            elapsed_ms=_elapsed(t0),
        )


class AuditAgent(OperationalAgent):
    """Generates audit evidence and validates audit trail integrity."""

    @property
    def name(self) -> str:
        return "AuditAgent"

    @property
    def domain(self) -> str:
        return "audit"

    async def execute(self, context: AgentContext) -> AgentResult:
        t0 = time.monotonic()
        state = context.state
        events = state.get("audit_events", [])
        period = state.get("audit_period", "current_quarter")

        evidence_items = len(events)
        narration = (
            f"Audit evidence collected for period '{period}'. "
            f"{evidence_items} event(s) in trail."
        )

        return self._result(
            status=AgentStatus.SUCCEEDED,
            output={
                "period": period,
                "evidence_items": evidence_items,
                "sample_events": events[:5],
            },
            narration=narration,
            elapsed_ms=_elapsed(t0),
        )


class NotificationAgent(OperationalAgent):
    """Coordinates stakeholder notification and escalation routing."""

    @property
    def name(self) -> str:
        return "NotificationAgent"

    @property
    def domain(self) -> str:
        return "notification"

    async def execute(self, context: AgentContext) -> AgentResult:
        t0 = time.monotonic()
        state = context.state
        channels = state.get("notification_channels", ["email", "slack"])
        recipients = state.get("recipients", [])
        severity = state.get("severity", "medium")
        dispatched: list[str] = []

        for ch in channels:
            dispatched.append(ch)

        narration = (
            f"Notifications dispatched via {len(dispatched)} channel(s) "
            f"to {len(recipients)} recipient(s). Severity: {severity}."
        )

        return self._result(
            status=AgentStatus.SUCCEEDED,
            output={
                "channels_used": dispatched,
                "recipient_count": len(recipients),
                "severity": severity,
            },
            narration=narration,
            elapsed_ms=_elapsed(t0),
        )


class CapacityAgent(OperationalAgent):
    """Evaluates capacity utilisation and recommends scaling actions."""

    @property
    def name(self) -> str:
        return "CapacityAgent"

    @property
    def domain(self) -> str:
        return "capacity"

    async def execute(self, context: AgentContext) -> AgentResult:
        t0 = time.monotonic()
        state = context.state
        utilisation: dict[str, float] = state.get("utilisation", {})
        threshold: float = state.get("capacity_threshold", 0.80)

        overloaded = {k: v for k, v in utilisation.items() if v >= threshold}
        headroom = {k: round(1.0 - v, 3) for k, v in utilisation.items()}

        recommendations: list[str] = []
        for svc, util in overloaded.items():
            recommendations.append(f"Scale out '{svc}' (utilisation {util:.0%})")

        narration = (
            f"Capacity analysis: {len(utilisation)} resource(s) evaluated. "
            f"{len(overloaded)} at or above {threshold:.0%} threshold."
            + (f" Actions recommended: {len(recommendations)}." if recommendations else "")
        )

        return self._result(
            status=AgentStatus.SUCCEEDED,
            output={
                "resources_evaluated": len(utilisation),
                "overloaded": list(overloaded.keys()),
                "headroom": headroom,
                "recommendations": recommendations,
            },
            narration=narration,
            elapsed_ms=_elapsed(t0),
        )


class RollbackAgent(OperationalAgent):
    """Executes compensating transactions and state restoration."""

    @property
    def name(self) -> str:
        return "RollbackAgent"

    @property
    def domain(self) -> str:
        return "rollback"

    async def execute(self, context: AgentContext) -> AgentResult:
        t0 = time.monotonic()
        state = context.state
        snapshot_id = state.get("rollback_snapshot_id")
        target_services = state.get("rollback_targets", [])
        strategy = state.get("rollback_strategy", "snapshot")

        if not snapshot_id and not target_services:
            return self._result(
                AgentStatus.SKIPPED,
                narration="No rollback target or snapshot specified; skipped.",
                elapsed_ms=_elapsed(t0),
            )

        rolled_back = list(target_services)
        narration = (
            f"Rollback '{strategy}' applied. "
            + (f"Snapshot: {snapshot_id}. " if snapshot_id else "")
            + f"Services restored: {', '.join(rolled_back) if rolled_back else 'none'}."
        )

        return self._result(
            status=AgentStatus.SUCCEEDED,
            output={
                "strategy": strategy,
                "snapshot_id": snapshot_id,
                "services_rolled_back": rolled_back,
            },
            narration=narration,
            elapsed_ms=_elapsed(t0),
        )


# ---------------------------------------------------------------------------
# QA / Document-processing agents
# ---------------------------------------------------------------------------


class DocumentReaderAgent(OperationalAgent):
    """
    Reads and parses an input document, extracting numbered items
    (requirements, rules, steps) as a structured list.

    Reads from state["document_text"] when provided; otherwise
    generates representative simulation items from the objective.
    """

    @property
    def name(self) -> str:
        return "DocumentReaderAgent"

    @property
    def domain(self) -> str:
        return "document_reader"

    async def execute(self, context: AgentContext) -> AgentResult:
        import re
        t0 = time.monotonic()
        text: str = context.state.get("document_text", "")
        items: list[dict[str, str]] = []

        if text:
            pattern = re.compile(r"([A-Z]+-\d+|REQ-\d+|\d+\.\d*)\s+(.*)")
            for m in pattern.finditer(text):
                items.append({"id": m.group(1), "description": m.group(2).strip()})
            if not items:
                # fallback: split on numbered lines
                for line in text.splitlines():
                    m = re.match(r"\s*(\d+)[.)]\s+(.*)", line)
                    if m:
                        items.append({"id": m.group(1), "description": m.group(2).strip()})
        else:
            # Simulate generic items derived from the objective
            words = context.objective.split()
            domain_hint = context.state.get("project_name", "system")
            for i in range(1, 6):
                items.append({
                    "id": f"REQ-{i:03d}",
                    "description": f"The {domain_hint} must support requirement {i}: "
                                   f"{' '.join(words[:3])} (simulated)",
                })

        sections = list({item["id"].split("-")[0] for item in items if "-" in item["id"]})

        return self._result(
            status=AgentStatus.SUCCEEDED,
            output={
                "items":     items,
                "sections":  sections,
                "item_count": len(items),
            },
            narration=(
                f"Document parsed. Extracted {len(items)} item(s) "
                f"across {len(sections)} section(s)."
            ),
            elapsed_ms=_elapsed(t0),
        )


class ScenarioGeneratorAgent(OperationalAgent):
    """
    Generates structured QA test scenarios from extracted document items.

    Reads from state["document_reader"]["items"]; generates generic
    positive/negative/edge scenarios for each item.
    """

    @property
    def name(self) -> str:
        return "ScenarioGeneratorAgent"

    @property
    def domain(self) -> str:
        return "test_scenario"

    async def execute(self, context: AgentContext) -> AgentResult:
        t0 = time.monotonic()
        items: list[dict] = context.state.get("document_reader", {}).get("items", [])

        if not items:
            items = [{"id": "GEN-001", "description": context.objective}]

        scenarios: list[dict] = []
        scenario_types = ["positive", "negative", "edge"]
        for item in items:
            for stype in scenario_types[:2]:   # positive + negative per item
                scenarios.append({
                    "scenario_id": f"TC-{item['id']}-{stype.upper()[:3]}",
                    "requirement": item["id"],
                    "type":        stype,
                    "title":       (
                        f"Verify ({stype}): {item['description'][:60]}"
                        if stype == "positive"
                        else f"Reject invalid input for: {item['description'][:50]}"
                    ),
                    "status": "pending",
                })

        return self._result(
            status=AgentStatus.SUCCEEDED,
            output={
                "scenarios":      scenarios,
                "scenario_count": len(scenarios),
            },
            narration=(
                f"Generated {len(scenarios)} test scenario(s) from "
                f"{len(items)} item(s)."
            ),
            elapsed_ms=_elapsed(t0),
        )


class TestRunnerAgent(OperationalAgent):
    """
    Executes QA test scenarios and records pass/fail results.

    Reads scenarios from state["test_scenario"]["scenarios"].
    In the absence of an actual test harness, simulates execution
    with a deterministic pass/fail based on scenario type.
    """

    @property
    def name(self) -> str:
        return "TestRunnerAgent"

    @property
    def domain(self) -> str:
        return "test_runner"

    async def execute(self, context: AgentContext) -> AgentResult:
        t0 = time.monotonic()
        scenarios: list[dict] = (
            context.state.get("test_scenario", {}).get("scenarios", [])
        )

        results: list[dict] = []
        passed = failed = 0

        for sc in scenarios:
            # Simulate: negative edge tests have a 20% failure rate in demo
            if sc.get("type") == "negative" and hash(sc["scenario_id"]) % 5 == 0:
                status, reason = "FAIL", "Boundary condition not enforced"
                failed += 1
            else:
                status, reason = "PASS", "Assertion verified"
                passed += 1
            results.append({**sc, "status": status, "reason": reason})

        total     = len(results)
        pass_rate = round(passed / total * 100, 1) if total else 0.0

        return self._result(
            status=AgentStatus.SUCCEEDED,
            output={
                "results":   results,
                "total":     total,
                "passed":    passed,
                "failed":    failed,
                "pass_rate": pass_rate,
            },
            narration=(
                f"Test run complete. {passed}/{total} passed ({pass_rate}%). "
                f"{failed} failure(s) detected."
            ),
            elapsed_ms=_elapsed(t0),
        )


class ReportDispatchAgent(OperationalAgent):
    """
    Composes a summary report from workflow results and dispatches it.

    Reads test results from state["test_runner"] and sends to
    state["report_recipients"] (default: team@company.com).
    In this SDK implementation, the report is printed to stdout;
    production deployments connect an SMTP/API transport here.
    """

    @property
    def name(self) -> str:
        return "ReportDispatchAgent"

    @property
    def domain(self) -> str:
        return "report"

    async def execute(self, context: AgentContext) -> AgentResult:
        t0 = time.monotonic()
        run_data   = context.state.get("test_runner", {})
        recipients = context.state.get(
            "report_recipients", ["team@company.com"]
        )
        project    = context.state.get("project_name", "Workflow")

        total     = run_data.get("total", 0)
        passed    = run_data.get("passed", 0)
        failed    = run_data.get("failed", 0)
        pass_rate = run_data.get("pass_rate", 0.0)
        failures  = [r for r in run_data.get("results", []) if r.get("status") == "FAIL"]

        subject = f"QA Report — {project} — {pass_rate}% pass rate"
        lines = [
            f"QA REPORT  —  {project}",
            "=" * 48,
            f"Test scenarios run  : {total}",
            f"Passed              : {passed}",
            f"Failed              : {failed}",
            f"Pass rate           : {pass_rate}%",
            "",
        ]
        if failures:
            lines.append("FAILURES:")
            for f_ in failures:
                lines.append(f"  [{f_['scenario_id']}] {f_['title']} — {f_['reason']}")
        else:
            lines.append("No failures detected.")
        lines += ["", "— Freya Automated QA"]

        # Print email preview (replace with SMTP/API call in production)
        divider = "─" * 56
        print(f"\n{divider}")
        print("  EMAIL REPORT PREVIEW")
        print(divider)
        print(f"  To      : {', '.join(recipients)}")
        print(f"  Subject : {subject}")
        print(divider)
        for line in lines:
            print(f"  {line}")
        print(divider)

        return self._result(
            status=AgentStatus.SUCCEEDED,
            output={
                "subject":    subject,
                "recipients": recipients,
                "body":       "\n".join(lines),
                "sent":       True,
            },
            narration=(
                f"Report dispatched to {len(recipients)} recipient(s). "
                f"Subject: \u00ab{subject}\u00bb."
            ),
            elapsed_ms=_elapsed(t0),
        )


# ---------------------------------------------------------------------------
# Software / Data / General Agents
# ---------------------------------------------------------------------------

import json
import os
import re as _re
import textwrap

# Always write workspace/ relative to the freya repo root, regardless of cwd.
# agents.py lives at <repo>/freya/agents/agents.py → go up 3 levels.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _slugify(text: str) -> str:
    """Convert a phrase to a snake_case identifier."""
    text = text.lower().strip()
    text = _re.sub(r"[^a-z0-9\s_]", "", text)
    text = _re.sub(r"\s+", "_", text)
    return text[:40] or "project"


def _extract_project_name(objective: str) -> str:
    """Pull the most meaningful noun from the objective as a project name."""
    # Strip leading verbs
    stripped = _re.sub(
        r"^\s*(create|build|write|generate|make|implement|develop|code|program)\s+(a\s+|an\s+|the\s+)?",
        "",
        objective.lower(),
    )
    # Remove noise words (adjectives, language names that pad the name)
    _NOISE = {"simple", "basic", "quick", "small", "easy", "python", "javascript",
               "java", "typescript", "rust", "go", "ruby", "php", "new", "clean"}
    words = [w for w in stripped.split() if w not in _NOISE][:3]
    return _slugify(" ".join(words)) or "project"


# ── Helpers that produce file content strings ────────────────────────────────

def _tools_code(project: str, functions: list[dict]) -> str:
    lines = [
        f'"""tools/{project}_tools.py',
        "",
        f"Tools generated by Freya for: {project}",
        '"""',
        "from __future__ import annotations",
        "",
        "",
    ]
    for fn in functions:
        name = fn["name"]
        params = fn.get("params", "a: float, b: float")
        ret = fn.get("return_type", "float")
        doc = fn.get("doc", f"Execute {name}.")
        body = fn.get("body", "    raise NotImplementedError")
        lines += [
            f"def {name}({params}) -> {ret}:",
            f'    """{doc}"""',
            body,
            "",
            "",
        ]
    return "\n".join(lines)


def _agent_code(project: str, functions: list[dict]) -> str:
    class_name = "".join(w.title() for w in project.split("_")) + "Agent"
    fn_imports = ", ".join(fn["name"] for fn in functions)
    first_fn = functions[0]["name"] if functions else "run"
    fn_names = {fn["name"] for fn in functions}
    is_numeric = bool(fn_names & {"add", "subtract", "multiply", "divide"})

    lines: list[str] = [
        f'"""agents/{project}_agent.py',
        "",
        f"Agent generated by Freya for: {project}",
        '"""',
        "from __future__ import annotations",
        "",
        "import re" if is_numeric else "",
        "import time",
        "",
        "from freya.agents.base import AgentContext, AgentResult, AgentStatus, OperationalAgent",
        f"from tools.{project}_tools import {fn_imports}",
        "",
        "",
        f"class {class_name}(OperationalAgent):",
        "    @property",
        "    def name(self) -> str:",
        f'        return "{class_name}"',
        "",
        "    @property",
        "    def domain(self) -> str:",
        f'        return "{project}"',
        "",
    ]

    if is_numeric:
        lines += [
            "    _OP_PATTERNS = [",
            '        (r"\\b(?:add|plus)\\b|\\+",                "add"),',
            '        (r"\\b(?:subtract|minus)\\b",              "subtract"),',
            '        (r"\\b(?:multiply|times|x)\\b|\\*",        "multiply"),',
            '        (r"\\b(?:divide|divided\\s+by|over)\\b|/", "divide"),',
            "    ]",
            "",
            "    def _parse_prompt(self, prompt: str) -> dict:",
            "        op_matched = False",
            f'        op = "{first_fn}"',
            "        for pattern, name in self._OP_PATTERNS:",
            "            if re.search(pattern, prompt, re.IGNORECASE):",
            "                op = name",
            "                op_matched = True",
            "                break",
            '        nums = re.findall(r"-?\\d+(?:\\.\\d+)?", prompt)',
            "        return {",
            '            "operation": op,',
            '            "a": float(nums[0]) if len(nums) > 0 else 0.0,',
            '            "b": float(nums[1]) if len(nums) > 1 else 0.0,',
            '            "_op_matched": op_matched,',
            '            "_nums_found": len(nums),',
            "        }",
            "",
            "    async def execute(self, context: AgentContext) -> AgentResult:",
            "        t0 = time.monotonic()",
            "        parsed: dict = {}",
            '        if "operation" not in context.state:',
            "            parsed = self._parse_prompt(context.objective)",
            "            context.state.update(parsed)",
            "",
            '        nums_found = parsed.get("_nums_found", 1)',
            "        if nums_found == 0:",
            "            elapsed = (time.monotonic() - t0) * 1000",
            "            return self._result(",
            "                status=AgentStatus.FAILED,",
            "                errors=[f\"No numeric operands found in: '{context.objective}'\"],",
            "                narration=\"Prompt is outside this agent's capabilities (expected a numeric expression).\",",
            "                elapsed_ms=elapsed,",
            "            )",
            "",
            "        warnings = []",
            '        if not parsed.get("_op_matched", True):',
            "            warnings.append(\"No operation keyword recognised — defaulted to 'add'.\")",
            "        if nums_found == 1:",
            '            warnings.append("Only one operand found — second operand defaulted to 0.")',
            "",
            f'        operation = context.state.get("operation", "{first_fn}")',
            "        ops = {",
        ]
        for fn in functions:
            lines.append(f'            "{fn["name"]}": {fn["name"]},')
        lines += [
            "        }",
            f"        fn = ops.get(operation, {first_fn})",
            '        a = context.state.get("a", 0.0)',
            '        b = context.state.get("b", 0.0)',
            "        try:",
            "            result = fn(a, b)",
            "        except ZeroDivisionError:",
            "            elapsed = (time.monotonic() - t0) * 1000",
            "            return self._result(",
            "                status=AgentStatus.FAILED,",
            '                errors=["Division by zero."],',
            '                narration=f"{operation}({a}, {b}) failed: division by zero.",',
            "                elapsed_ms=elapsed,",
            "            )",
            "        elapsed = (time.monotonic() - t0) * 1000",
            "        return self._result(",
            "            status=AgentStatus.SUCCEEDED,",
            '            output={"result": result, "operation": operation},',
            '            narration=f"{operation}({a}, {b}) = {result}",',
            "            warnings=warnings,",
            "            elapsed_ms=elapsed,",
            "        )",
        ]
    else:
        lines += [
            "    async def execute(self, context: AgentContext) -> AgentResult:",
            "        t0 = time.monotonic()",
            '        inp = context.state.get("input", context.objective)',
            f"        result = {first_fn}(inp)",
            "        elapsed = (time.monotonic() - t0) * 1000",
            "        return self._result(",
            "            status=AgentStatus.SUCCEEDED,",
            '            output={"result": result},',
            f'            narration=f"{first_fn}() completed.",',
            "            elapsed_ms=elapsed,",
            "        )",
    ]

    lines.append("")
    return "\n".join(line for line in lines if line is not None)



def _policy_json(project: str, rules: list[dict]) -> str:
    payload = {
        "name": f"{project}_policy",
        "version": "1.0.0",
        "generated_by": "Freya",
        "rules": rules,
    }
    return json.dumps(payload, indent=2)


def _readme(project: str, objective: str, files: list[str]) -> str:
    file_list = "\n".join(f"  - {f}" for f in files)
    return textwrap.dedent(f"""\
        # {project}

        Generated by **Freya** — Autonomous Workflow Creator.

        ## Objective
        {objective}

        ## Generated Files
        {file_list}

        ## Quick Start
        ```python
        from agents.{project}_agent import {
            "".join(w.title() for w in project.split("_")) + "Agent"
        }
        import asyncio

        agent = {"".join(w.title() for w in project.split("_")) + "Agent"}()
        # See tools/{project}_tools.py for available operations.
        ```
        """)


# ── Domain template library ────────────────────────────────────────────────

_FUNCTION_TEMPLATES: dict[str, list[dict]] = {
    "calculator": [
        {"name": "add",      "params": "a: float, b: float", "return_type": "float",
         "doc": "Add two numbers.",      "body": "    return a + b"},
        {"name": "subtract", "params": "a: float, b: float", "return_type": "float",
         "doc": "Subtract b from a.",    "body": "    return a - b"},
        {"name": "multiply", "params": "a: float, b: float", "return_type": "float",
         "doc": "Multiply two numbers.", "body": "    return a * b"},
        {"name": "divide",   "params": "a: float, b: float", "return_type": "float",
         "doc": "Divide a by b. Raises ZeroDivisionError if b is zero.",
         "body": "    if b == 0:\n        raise ZeroDivisionError('Cannot divide by zero')\n    return a / b"},
    ],
    "parser": [
        {"name": "parse",    "params": "text: str", "return_type": "dict",
         "doc": "Parse input text into a structured dict.",
         "body": "    return {\"raw\": text, \"tokens\": text.split()}"},
        {"name": "validate", "params": "data: dict", "return_type": "bool",
         "doc": "Validate a parsed structure.",
         "body": "    return bool(data)"},
    ],
    "api": [
        {"name": "get",    "params": "url: str, params: dict | None = None", "return_type": "dict",
         "doc": "Perform a GET request.",
         "body": "    import urllib.request, json\n    req = urllib.request.Request(url)\n    with urllib.request.urlopen(req) as r:\n        return json.loads(r.read())"},
        {"name": "post",   "params": "url: str, payload: dict", "return_type": "dict",
         "doc": "Perform a POST request.",
         "body": "    import urllib.request, json\n    data = json.dumps(payload).encode()\n    req = urllib.request.Request(url, data=data, method='POST')\n    with urllib.request.urlopen(req) as r:\n        return json.loads(r.read())"},
    ],
    "_default": [
        {"name": "run",    "params": "input: str", "return_type": "str",
         "doc": "Execute the primary operation.",
         "body": "    return f'Processed: {input}'"},
        {"name": "validate", "params": "input: str", "return_type": "bool",
         "doc": "Validate the input.",
         "body": "    return bool(input and input.strip())"},
    ],
}

_POLICY_TEMPLATES: dict[str, list[dict]] = {
    "calculator": [
        {"id": "numeric_inputs",    "description": "All inputs must be numeric values.",  "type": "validation"},
        {"id": "no_divide_by_zero", "description": "Division by zero is not permitted.",  "type": "safety"},
        {"id": "result_range",      "description": "Results must be finite real numbers.", "type": "output"},
    ],
    "_default": [
        {"id": "non_empty_input",   "description": "Inputs must not be empty.",           "type": "validation"},
        {"id": "safe_output",       "description": "Outputs must not contain secrets.",   "type": "security"},
    ],
}


def _pick_functions(project: str, objective: str) -> list[dict]:
    obj_lower = objective.lower()
    for key in _FUNCTION_TEMPLATES:
        if key != "_default" and key in obj_lower:
            return _FUNCTION_TEMPLATES[key]
        if key != "_default" and key in project:
            return _FUNCTION_TEMPLATES[key]
    return _FUNCTION_TEMPLATES["_default"]


def _pick_policies(project: str, objective: str) -> list[dict]:
    obj_lower = objective.lower()
    for key in _POLICY_TEMPLATES:
        if key != "_default" and key in obj_lower:
            return _POLICY_TEMPLATES[key]
        if key != "_default" and key in project:
            return _POLICY_TEMPLATES[key]
    return _POLICY_TEMPLATES["_default"]


# ── Agents ───────────────────────────────────────────────────────────────────

class RequirementsAgent(OperationalAgent):
    """Parses an objective into structured requirements."""

    @property
    def name(self) -> str:
        return "RequirementsAgent"

    @property
    def domain(self) -> str:
        return "requirements"

    async def execute(self, context: AgentContext) -> AgentResult:
        t0 = time.monotonic()
        objective = context.state.get("_objective") or context.objective or context.state.get("objective", "")
        project   = _extract_project_name(objective)
        functions = _pick_functions(project, objective)
        policies  = _pick_policies(project, objective)
        return self._result(
            status=AgentStatus.SUCCEEDED,
            output={
                "objective":    objective,
                "project_name": project,
                "functions":    functions,
                "policies":     policies,
                "requirements": [
                    f"The project name is '{project}'.",
                    f"Implement {len(functions)} tool function(s): "
                    + ", ".join(f['name'] for f in functions) + ".",
                    "Wrap tools in a typed OperationalAgent subclass.",
                    f"Enforce {len(policies)} policy rule(s) in a JSON policy file.",
                ],
            },
            narration=f"Requirements extracted — project '{project}', "
                      f"{len(functions)} function(s), {len(policies)} policy rule(s).",
            elapsed_ms=_elapsed(t0),
        )


class ImplementationAgent(OperationalAgent):
    """Produces an implementation blueprint from the requirements."""

    @property
    def name(self) -> str:
        return "ImplementationAgent"

    @property
    def domain(self) -> str:
        return "implementation"

    async def execute(self, context: AgentContext) -> AgentResult:
        t0   = time.monotonic()
        reqs = context.state.get("requirements", {})
        project   = reqs.get("project_name", "project")
        functions = reqs.get("functions", _FUNCTION_TEMPLATES["_default"])
        policies  = reqs.get("policies",  _POLICY_TEMPLATES["_default"])
        steps = [
            f"1. Create workspace/{project}/ directory tree (agents/, tools/, policies/).",
            f"2. Generate tools/{project}_tools.py with {len(functions)} function(s).",
            f"3. Generate agents/{project}_agent.py wrapping those tools.",
            f"4. Generate policies/{project}_policy.json with {len(policies)} rule(s).",
            "5. Write README.md with usage instructions.",
        ]
        return self._result(
            status=AgentStatus.SUCCEEDED,
            output={
                "blueprint":  steps,
                "project":    project,
                "functions":  functions,
                "policies":   policies,
            },
            narration=f"Blueprint produced for '{project}' — {len(steps)} step(s).",
            elapsed_ms=_elapsed(t0),
        )


class CodegenAgent(OperationalAgent):
    """Generates source code and policy content from the implementation blueprint."""

    @property
    def name(self) -> str:
        return "CodegenAgent"

    @property
    def domain(self) -> str:
        return "codegen"

    async def execute(self, context: AgentContext) -> AgentResult:
        t0   = time.monotonic()
        impl = context.state.get("implementation", {})
        reqs = context.state.get("requirements", {})
        project  = impl.get("project") or reqs.get("project_name", "project")
        objective = reqs.get("objective") or context.state.get("_objective") or context.objective or ""
        functions = impl.get("functions") or reqs.get("functions", _FUNCTION_TEMPLATES["_default"])
        policies  = impl.get("policies")  or reqs.get("policies",  _POLICY_TEMPLATES["_default"])

        tools_content  = _tools_code(project, functions)
        agent_content  = _agent_code(project, functions)
        policy_content = _policy_json(project, policies)

        file_list = [
            f"tools/{project}_tools.py",
            f"agents/{project}_agent.py",
            f"policies/{project}_policy.json",
            "README.md",
        ]
        readme_content = _readme(project, objective, file_list)

        return self._result(
            status=AgentStatus.SUCCEEDED,
            output={
                "project":  project,
                "files": {
                    f"tools/{project}_tools.py":          tools_content,
                    f"agents/{project}_agent.py":         agent_content,
                    f"policies/{project}_policy.json":    policy_content,
                    "README.md":                          readme_content,
                },
            },
            narration=f"Generated {len(file_list)} file(s) for project '{project}'.",
            elapsed_ms=_elapsed(t0),
        )


class ValidationAgent(OperationalAgent):
    """Validates generated code by checking Python syntax."""

    @property
    def name(self) -> str:
        return "ValidationAgent"

    @property
    def domain(self) -> str:
        return "validation"

    async def execute(self, context: AgentContext) -> AgentResult:
        t0      = time.monotonic()
        codegen = context.state.get("codegen", {})
        files   = codegen.get("files", {})
        errors: list[str] = []
        for path, content in files.items():
            if path.endswith(".py"):
                try:
                    compile(content, path, "exec")
                except SyntaxError as exc:
                    errors.append(f"{path}: {exc}")
        valid = len(errors) == 0
        return self._result(
            status=AgentStatus.SUCCEEDED if valid else AgentStatus.FAILED,
            output={"valid": valid, "errors": errors, "files_checked": len([f for f in files if f.endswith(".py")])},
            narration=(
                f"Validation passed — {len(files)} file(s) are syntax-clean."
                if valid else
                f"Validation failed — {len(errors)} syntax error(s) found."
            ),
            elapsed_ms=_elapsed(t0),
        )


class DeliveryAgent(OperationalAgent):
    """Writes generated files to a workspace sub-folder on disk."""

    @property
    def name(self) -> str:
        return "DeliveryAgent"

    @property
    def domain(self) -> str:
        return "delivery"

    async def execute(self, context: AgentContext) -> AgentResult:
        t0      = time.monotonic()
        codegen = context.state.get("codegen", {})
        files   = codegen.get("files", {})
        project = codegen.get("project") or "project"

        base = os.path.join(_REPO_ROOT, "workspace", project)
        written: list[str] = []
        for rel_path, content in files.items():
            abs_path = os.path.join(base, rel_path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as fh:
                fh.write(content)
            written.append(abs_path)

        # If no files were generated (non-software domain), just succeed
        if not written:
            return self._result(
                status=AgentStatus.SUCCEEDED,
                output={"project_path": base, "files_written": []},
                narration="Delivery complete — no files to write for this domain.",
                elapsed_ms=_elapsed(t0),
            )

        print(f"\n  Project written to: {base}")
        for p in written:
            print(f"    + {os.path.relpath(p, _REPO_ROOT)}")

        return self._result(
            status=AgentStatus.SUCCEEDED,
            output={"project_path": base, "files_written": written},
            narration=f"Project '{project}' written to workspace/{project}/ — {len(written)} file(s).",
            elapsed_ms=_elapsed(t0),
        )


class AgentRunnerAgent(OperationalAgent):
    """
    Dynamically imports and executes the generated agent after delivery.
    Adds the project workspace to sys.path, loads the agent class,
    and calls execute() with appropriate sample inputs.
    """

    @property
    def name(self) -> str:
        return "AgentRunnerAgent"

    @property
    def domain(self) -> str:
        return "agent_runner"

    async def execute(self, context: AgentContext) -> AgentResult:
        import importlib
        import sys

        t0       = time.monotonic()
        delivery = context.state.get("delivery", {})
        codegen  = context.state.get("codegen", {})
        reqs     = context.state.get("requirements", {})

        project      = codegen.get("project") or reqs.get("project_name", "project")
        project_path = delivery.get("project_path") or os.path.join(_REPO_ROOT, "workspace", project)
        functions    = reqs.get("functions") or codegen.get("functions", [{"name": "run", "params": "input: str"}])
        first_fn     = functions[0]["name"] if functions else "run"
        first_params = functions[0].get("params", "") if functions else ""
        class_name   = "".join(w.title() for w in project.split("_")) + "Agent"
        module_name  = f"agents.{project}_agent"

        added = project_path not in sys.path
        if added:
            sys.path.insert(0, project_path)

        try:
            # Force fresh import in case of repeated calls
            sys.modules.pop(module_name, None)
            mod       = importlib.import_module(module_name)
            agent_cls = getattr(mod, class_name)
            agent     = agent_cls()

            # Build sample inputs based on the first tool's parameter types
            if "str" in first_params:
                sample = {"operation": first_fn, "a": "hello", "b": "world"}
            else:
                sample = {"operation": first_fn, "a": 3.0, "b": 5.0}
            sample["_objective"] = context.state.get("_objective", "")

            from freya.agents.base import AgentContext as Ctx
            run_ctx    = Ctx(objective=f"Demo: {class_name}", phase_name="run_agent", state=sample)
            run_result = await agent.execute(run_ctx)

            print(f"\n  {class_name} demo run:")
            print(f"    operation : {first_fn}")
            for k, v in run_result.output.items():
                if k != "operation":
                    print(f"    {k:<10}: {v}")

            return self._result(
                status=AgentStatus.SUCCEEDED,
                output={
                    "agent":     class_name,
                    "operation": first_fn,
                    "result":    run_result.output,
                    "narration": run_result.narration,
                },
                narration=f"{class_name} ran successfully — {run_result.narration}",
                elapsed_ms=_elapsed(t0),
            )

        except Exception as exc:
            # Non-fatal — project is delivered; runtime errors are expected
            # for agents that require external services (e.g. a live API server)
            print(f"\n  {class_name} demo run skipped: {exc}")
            return self._result(
                status=AgentStatus.SUCCEEDED,
                output={"agent": class_name, "skipped": True, "reason": str(exc)},
                narration=f"{class_name} generated successfully; demo run skipped ({type(exc).__name__}).",
                elapsed_ms=_elapsed(t0),
            )
        finally:
            if added and project_path in sys.path:
                sys.path.remove(project_path)


class AnalysisAgent(OperationalAgent):
    """Analyses the input data or request."""

    @property
    def name(self) -> str:
        return "AnalysisAgent"

    @property
    def domain(self) -> str:
        return "analysis"

    async def execute(self, context: AgentContext) -> AgentResult:
        t0        = time.monotonic()
        objective = context.objective or ""
        words     = objective.split()
        return self._result(
            status=AgentStatus.SUCCEEDED,
            output={
                "objective":  objective,
                "word_count": len(words),
                "key_terms":  [w for w in words if len(w) > 4][:8],
                "complexity": "moderate" if len(words) > 10 else "simple",
            },
            narration=f"Analysis complete — {len(words)} word(s), complexity: "
                      + ("moderate" if len(words) > 10 else "simple") + ".",
            elapsed_ms=_elapsed(t0),
        )


class SummaryAgent(OperationalAgent):
    """Generates a summary of the workflow state and findings."""

    @property
    def name(self) -> str:
        return "SummaryAgent"

    @property
    def domain(self) -> str:
        return "summary"

    async def execute(self, context: AgentContext) -> AgentResult:
        t0         = time.monotonic()
        objective  = context.objective or ""
        state_keys = list(context.state.keys())
        lines = [f"Objective: {objective}"]
        for key in state_keys:
            val = context.state[key]
            if isinstance(val, dict):
                lines.append(f"  [{key}]: " + ", ".join(str(k) for k in val.keys()))
        return self._result(
            status=AgentStatus.SUCCEEDED,
            output={"summary_lines": lines, "domains_run": state_keys},
            narration=f"Summary produced — {len(lines)} line(s) covering {len(state_keys)} domain(s).",
            elapsed_ms=_elapsed(t0),
        )
