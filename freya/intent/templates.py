"""freya/intent/templates.py

Reusable workflow archetypes for common operational domains.

Each template defines:
  - canonical subworkflows (in human language)
  - governance defaults
  - execution strategy hint
  - clarification fields

No DAG, no runtime mechanics — pure intent-level description.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class WorkflowTemplate:
    """Archetype definition for a workflow domain."""

    template_id: str
    domain: str
    display_name: str
    description: str
    subworkflows: list[str]                      # human-readable step names
    governance_requirements: list[str]           # e.g. ["budget_approval"]
    recommended_strategy: str                    # "deterministic" | "cognitive" | "hybrid"
    estimated_complexity: str                    # "simple" | "moderate" | "complex"
    required_entities: list[str]                 # fields needed to run (for clarification)
    optional_entities: list[str] = field(default_factory=list)
    constraint_defaults: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Template registry
# ---------------------------------------------------------------------------

BUSINESS_TRAVEL_TEMPLATE = WorkflowTemplate(
    template_id="business_travel",
    domain="business_travel",
    display_name="Business Trip Planner",
    description="Books flights, hotels, and meeting itineraries for business travel.",
    subworkflows=[
        "Search Flights",
        "Find Hotels",
        "Compare & Select Hotel",
        "Build Meeting Itinerary",
        "Estimate Total Costs",
    ],
    governance_requirements=["budget_approval_if_hotel_over_limit"],
    recommended_strategy="hybrid",               # deterministic-first, cognitive for hotel comparison
    estimated_complexity="moderate",
    required_entities=["destination"],
    optional_entities=["budget", "dates", "hotel_preference", "origin"],
    constraint_defaults={"budget_inr": 40_000, "nights": 2},
    tags=["travel", "booking", "itinerary"],
)

INCIDENT_RESPONSE_TEMPLATE = WorkflowTemplate(
    template_id="incident_response",
    domain="incident_response",
    display_name="Incident Response Coordinator",
    description="Diagnoses, triages, and coordinates resolution of operational incidents.",
    subworkflows=[
        "Diagnose Incident",
        "Assess Impact",
        "Notify Stakeholders",
        "Apply Remediation",
        "Verify Resolution",
        "Generate Post-Mortem",
    ],
    governance_requirements=["escalation_approval_for_p0", "stakeholder_notification"],
    recommended_strategy="cognitive",
    estimated_complexity="complex",
    required_entities=["incident_description"],
    optional_entities=["severity", "affected_systems", "team"],
    constraint_defaults={"max_resolution_time_hours": 4},
    tags=["operations", "incidents", "reliability"],
)

DATA_PIPELINE_TEMPLATE = WorkflowTemplate(
    template_id="data_pipeline",
    domain="data_pipeline",
    display_name="Data Pipeline Orchestrator",
    description="Ingests, transforms, validates, and loads data between systems.",
    subworkflows=[
        "Extract Source Data",
        "Validate Schema",
        "Transform & Enrich",
        "Load to Destination",
        "Verify Data Quality",
    ],
    governance_requirements=["data_quality_gate", "pii_handling_approval"],
    recommended_strategy="deterministic",
    estimated_complexity="moderate",
    required_entities=["source", "destination"],
    optional_entities=["schedule", "transformations", "quality_threshold"],
    constraint_defaults={"quality_threshold_pct": 99},
    tags=["data", "etl", "pipeline"],
)

SCHEDULING_TEMPLATE = WorkflowTemplate(
    template_id="scheduling",
    domain="scheduling",
    display_name="Meeting & Resource Scheduler",
    description="Coordinates calendars, rooms, and resources for meetings or events.",
    subworkflows=[
        "Check Attendee Availability",
        "Find Available Slots",
        "Reserve Resources",
        "Send Invitations",
        "Confirm Bookings",
    ],
    governance_requirements=["calendar_access_approval"],
    recommended_strategy="deterministic",
    estimated_complexity="simple",
    required_entities=["attendees", "duration"],
    optional_entities=["location", "agenda", "deadline"],
    constraint_defaults={},
    tags=["calendar", "meetings", "resources"],
)

PROCUREMENT_TEMPLATE = WorkflowTemplate(
    template_id="procurement",
    domain="procurement",
    display_name="Procurement Request Manager",
    description="Handles purchase requests through approval, sourcing, and order placement.",
    subworkflows=[
        "Validate Request",
        "Source Vendors",
        "Compare Quotes",
        "Obtain Approval",
        "Place Order",
        "Track Delivery",
    ],
    governance_requirements=["budget_approval", "vendor_approval_above_threshold"],
    recommended_strategy="hybrid",
    estimated_complexity="complex",
    required_entities=["item", "quantity"],
    optional_entities=["budget", "deadline", "preferred_vendor"],
    constraint_defaults={"approval_threshold_inr": 10_000},
    tags=["procurement", "purchasing", "approval"],
)


# ---------------------------------------------------------------------------
# Template registry lookup
# ---------------------------------------------------------------------------

TEMPLATE_REGISTRY: dict[str, WorkflowTemplate] = {
    t.template_id: t
    for t in [
        BUSINESS_TRAVEL_TEMPLATE,
        INCIDENT_RESPONSE_TEMPLATE,
        DATA_PIPELINE_TEMPLATE,
        SCHEDULING_TEMPLATE,
        PROCUREMENT_TEMPLATE,
    ]
}


def get_template(template_id: str) -> WorkflowTemplate | None:
    return TEMPLATE_REGISTRY.get(template_id)


def list_templates() -> list[WorkflowTemplate]:
    return list(TEMPLATE_REGISTRY.values())
