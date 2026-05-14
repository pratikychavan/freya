"""freya/workflows/planner.py

WorkflowPlanner — converts a free-text objective into a WorkflowPlan.

Domain detection is keyword-based with priority ordering:
  software > data > incident > recovery > migration > compliance >
  capacity > surge > qa_pipeline > general

No LLM required — deterministic keyword matching and phase templates.
"""
from __future__ import annotations

import re
from typing import Any

from freya.workflows.plan import WorkflowPhase, WorkflowPlan


# ---------------------------------------------------------------------------
# Domain keyword map — order defines priority
# ---------------------------------------------------------------------------

_DOMAIN_KEYWORDS: list[tuple[str, list[str]]] = [
    ("software",    ["create", "build", "write", "generate", "code", "implement", "develop",
                     "make", "program", "script", "function", "class", "module",
                     "calculator", "app", "application", "tool", "widget", "parser",
                     "api", "service", "library", "package"]),
    ("data",        ["analyze", "analyse", "report", "dashboard", "visualize", "visualise",
                     "aggregate", "dataset", "etl", "transform", "export", "import",
                     "csv", "json", "statistics", "insights", "chart", "graph"]),
    ("incident",    ["incident", "outage", "down", "failure", "alert", "degraded", "p0", "p1"]),
    ("recovery",    ["recover", "restore", "rollback", "revert", "undo", "fix"]),
    ("migration",   ["migrat", "deploy", "release", "cutover", "upgrade", "promote"]),
    ("compliance",  ["comply", "compliance", "audit", "regulation", "gdpr", "soc2", "iso", "framework"]),
    ("capacity",    ["capacity", "scale", "utilisation", "utilization", "resource", "cpu", "memory"]),
    ("surge",       ["surge", "spike", "peak", "traffic", "load", "queue"]),
    ("qa_pipeline", ["brd", "qa", "test scenario", "test case", "quality assurance", "test run",
                     "requirements document", "unit test", "integration test", "test report"]),
]

# ---------------------------------------------------------------------------
# Phase templates per domain
# ---------------------------------------------------------------------------

_DOMAIN_PHASES: dict[str, list[dict[str, Any]]] = {
    "software": [
        {
            "name": "understand_requirements",
            "description": "Parse the objective and produce a structured requirements summary.",
            "required_agent_domains": ["requirements"],
            "narration": "Analysing objective and structuring requirements.",
        },
        {
            "name": "design_solution",
            "description": "Design the solution: components, interfaces, and file layout.",
            "required_agent_domains": ["implementation"],
            "narration": "Designing solution layout and component interfaces.",
        },
        {
            "name": "generate_code",
            "description": "Generate source files: agents, tools, and policies.",
            "required_agent_domains": ["codegen"],
            "narration": "Generating agents, tools, and policy files.",
        },
        {
            "name": "deliver_project",
            "description": "Write all generated files to the workspace folder.",
            "required_agent_domains": ["delivery"],
            "narration": "Writing generated project files to disk.",
        },
        {
            "name": "run_agent",
            "description": "Dynamically import and execute the generated agent with sample inputs.",
            "required_agent_domains": ["agent_runner"],
            "narration": "Running the generated agent to verify it works.",
        },
    ],
    "data": [
        {
            "name": "collect_data",
            "description": "Identify and gather the relevant data sources and inputs.",
            "required_agent_domains": ["analysis"],
            "narration": "Collecting and cataloguing data sources.",
        },
        {
            "name": "process_and_transform",
            "description": "Clean, transform, and structure the collected data.",
            "required_agent_domains": ["analysis"],
            "narration": "Processing and transforming raw data.",
        },
        {
            "name": "generate_insights",
            "description": "Derive insights, statistics, and key findings from the data.",
            "required_agent_domains": ["summary"],
            "narration": "Generating insights and findings from processed data.",
        },
        {
            "name": "deliver_report",
            "description": "Compose and deliver the final data report.",
            "required_agent_domains": ["delivery"],
            "narration": "Composing and delivering the data report.",
        },
    ],
    "incident": [
        {
            "name": "detect_and_triage",
            "description": "Identify impacted services and classify incident severity.",
            "required_agent_domains": ["risk", "infrastructure"],
            "narration": "Detecting impacted services and classifying severity.",
        },
        {
            "name": "notify_stakeholders",
            "description": "Dispatch alerts to on-call responders and stakeholders.",
            "required_agent_domains": ["notification"],
            "narration": "Notifying on-call teams and stakeholders.",
        },
        {
            "name": "execute_recovery",
            "description": "Apply recovery playbook to restore affected services.",
            "required_agent_domains": ["recovery"],
            "narration": "Executing recovery playbook.",
        },
        {
            "name": "post_incident_audit",
            "description": "Record incident timeline and evidence for post-mortem.",
            "required_agent_domains": ["audit", "compliance"],
            "narration": "Recording audit evidence for post-mortem review.",
        },
    ],
    "recovery": [
        {
            "name": "assess_state",
            "description": "Assess current system state before rollback.",
            "required_agent_domains": ["infrastructure", "risk"],
            "narration": "Assessing current system state.",
        },
        {
            "name": "plan_rollback",
            "description": "Select rollback strategy and snapshot targets.",
            "required_agent_domains": ["rollback"],
            "narration": "Planning rollback strategy.",
        },
        {
            "name": "execute_rollback",
            "description": "Apply rollback and verify service restoration.",
            "required_agent_domains": ["rollback", "recovery"],
            "narration": "Executing rollback and verifying restoration.",
        },
        {
            "name": "validate_and_audit",
            "description": "Validate post-rollback state and record audit trail.",
            "required_agent_domains": ["compliance", "audit"],
            "narration": "Validating restored state and recording audit evidence.",
        },
    ],
    "migration": [
        {
            "name": "pre_migration_compliance",
            "description": "Evaluate compliance posture before migration.",
            "required_agent_domains": ["compliance"],
            "narration": "Evaluating compliance posture.",
        },
        {
            "name": "infrastructure_readiness",
            "description": "Validate target infrastructure health and capacity.",
            "required_agent_domains": ["infrastructure", "capacity"],
            "narration": "Validating target infrastructure readiness.",
        },
        {
            "name": "review_and_confirm",
            "description": "Review migration plan and confirm readiness before cutover.",
            "required_agent_domains": ["audit"],
            "narration": "Reviewing migration plan for completeness.",
        },
        {
            "name": "execute_migration",
            "description": "Execute migration steps with rollback safety.",
            "required_agent_domains": ["infrastructure", "rollback"],
            "narration": "Executing migration with rollback safety net.",
        },
        {
            "name": "post_migration_audit",
            "description": "Verify migration outcome and record evidence.",
            "required_agent_domains": ["audit", "compliance"],
            "narration": "Auditing migration outcome.",
        },
    ],
    "compliance": [
        {
            "name": "framework_assessment",
            "description": "Evaluate posture against relevant frameworks.",
            "required_agent_domains": ["compliance"],
            "narration": "Evaluating compliance frameworks.",
        },
        {
            "name": "risk_evaluation",
            "description": "Assess compliance-related risk exposure.",
            "required_agent_domains": ["risk"],
            "narration": "Assessing risk from compliance gaps.",
        },
        {
            "name": "collect_audit_evidence",
            "description": "Gather evidence for audit reporting.",
            "required_agent_domains": ["audit"],
            "narration": "Collecting and packaging audit evidence.",
        },
        {
            "name": "remediation_notification",
            "description": "Notify owners of remediation requirements.",
            "required_agent_domains": ["notification"],
            "narration": "Notifying owners of required remediations.",
        },
    ],
    "capacity": [
        {
            "name": "utilisation_analysis",
            "description": "Measure current utilisation across resources.",
            "required_agent_domains": ["capacity", "infrastructure"],
            "narration": "Analysing resource utilisation.",
        },
        {
            "name": "scaling_recommendation",
            "description": "Generate scaling recommendations and cost impact.",
            "required_agent_domains": ["capacity"],
            "narration": "Generating scaling recommendations.",
        },
        {
            "name": "notify_scaling_actions",
            "description": "Notify teams of recommended scaling actions.",
            "required_agent_domains": ["notification"],
            "narration": "Notifying teams of scaling recommendations.",
        },
    ],
    "surge": [
        {
            "name": "surge_detection",
            "description": "Detect and quantify traffic surge.",
            "required_agent_domains": ["capacity", "infrastructure"],
            "narration": "Detecting and quantifying surge.",
        },
        {
            "name": "load_redistribution",
            "description": "Redistribute load across available capacity.",
            "required_agent_domains": ["capacity"],
            "narration": "Redistributing load to absorb surge.",
        },
        {
            "name": "notify_teams",
            "description": "Notify operations teams of surge event.",
            "required_agent_domains": ["notification"],
            "narration": "Notifying operations teams.",
        },
    ],
    "qa_pipeline": [
        {
            "name": "read_document",
            "description": "Read and parse the input document to extract requirements or items.",
            "required_agent_domains": ["document_reader"],
            "narration": "Reading and parsing input document.",
        },
        {
            "name": "generate_test_scenarios",
            "description": "Generate QA test scenarios from extracted items.",
            "required_agent_domains": ["test_scenario"],
            "narration": "Generating test scenarios from requirements.",
        },
        {
            "name": "run_tests",
            "description": "Execute all test scenarios and record pass/fail results.",
            "required_agent_domains": ["test_runner"],
            "narration": "Executing test scenarios.",
        },
        {
            "name": "send_report",
            "description": "Compose QA summary report and dispatch to stakeholders.",
            "required_agent_domains": ["report"],
            "narration": "Composing and dispatching QA report.",
        },
    ],
    "general": [
        {
            "name": "analyse_request",
            "description": "Analyse the request and identify key objectives and constraints.",
            "required_agent_domains": ["analysis"],
            "narration": "Analysing the request and identifying objectives.",
        },
        {
            "name": "plan_execution",
            "description": "Produce a detailed execution plan for the request.",
            "required_agent_domains": ["implementation"],
            "narration": "Planning execution steps.",
        },
        {
            "name": "execute_and_validate",
            "description": "Execute the plan and validate the outcome.",
            "required_agent_domains": ["implementation", "validation"],
            "narration": "Executing plan and validating results.",
        },
        {
            "name": "summarise_results",
            "description": "Summarise results and package the deliverable.",
            "required_agent_domains": ["summary", "delivery"],
            "narration": "Summarising results and preparing deliverable.",
        },
    ],
}


def _detect_domain(objective: str) -> str:
    text = objective.lower()
    for domain, keywords in _DOMAIN_KEYWORDS:
        if any(re.search(r'\b' + kw, text) for kw in keywords):
            return domain
    return "general"


class WorkflowPlanner:
    """
    Converts a free-text objective into a WorkflowPlan.

    No LLM required — uses deterministic domain detection and
    pre-defined phase templates.
    """

    def plan(
        self,
        objective: str,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowPlan:
        """Generate a WorkflowPlan for the given objective string."""
        domain = _detect_domain(objective)
        phase_templates = _DOMAIN_PHASES.get(domain, _DOMAIN_PHASES["general"])

        phases: list[WorkflowPhase] = []
        all_agents: set[str] = set()
        for tpl in phase_templates:
            phase = WorkflowPhase(
                name=tpl["name"],
                description=tpl["description"],
                required_agent_domains=list(tpl["required_agent_domains"]),
                narration=tpl.get("narration", ""),
            )
            phases.append(phase)
            all_agents.update(tpl["required_agent_domains"])

        return WorkflowPlan(
            objective=objective,
            domain=domain,
            phases=phases,
            agents=sorted(all_agents),
            metadata=metadata or {},
        )
