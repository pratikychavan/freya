"""freya/intent/clarification.py

Decides when clarification is genuinely needed and formulates the
minimum questions required to unblock workflow synthesis.

Design principles:
  - NO chatbot loops — ask once, and only when required.
  - Only trigger when: ambiguity_score > AMBIGUITY_THRESHOLD **or**
    a required entity listed in the template is missing from the intent.
  - At most one question per missing field (no piling on).
"""
from __future__ import annotations

from freya.intent.models import ClarificationQuestion, UserIntent
from freya.intent.templates import WorkflowTemplate, get_template

# Ambiguity score above which clarification is triggered (regardless of entities)
AMBIGUITY_THRESHOLD = 0.5

# Per-domain question definitions -------------------------------------------
# Each entry: (field, question, reason, options | None)
# Evaluated in order; only triggered when the field is absent/empty.
_DOMAIN_QUESTIONS: dict[str, list[tuple[str, str, str, list[str] | None]]] = {
    "business_travel": [
        (
            "destination",
            "Which city are you travelling to?",
            "Destination is required to search for flights and hotels.",
            None,
        ),
        (
            "budget_inr",
            "What is your total travel budget? (e.g. ₹40,000)",
            "Budget drives flight-class and hotel-tier selection.",
            None,
        ),
        (
            "nights",
            "How many nights will you be staying?",
            "Duration is needed to price hotels accurately.",
            ["1 night", "2 nights", "3 nights", "4+ nights"],
        ),
    ],
    "incident_response": [
        (
            "incident_description",
            "Can you briefly describe the incident or system affected?",
            "A concrete description focuses triage and escalation.",
            None,
        ),
        (
            "severity",
            "What is the incident severity?",
            "Severity determines escalation paths and SLAs.",
            ["P0 - Critical", "P1 - High", "P2 - Medium", "P3 - Low"],
        ),
    ],
    "data_pipeline": [
        (
            "source",
            "What is the data source? (e.g. Postgres, S3, API endpoint)",
            "Source system drives connector and extraction strategy.",
            None,
        ),
        (
            "destination",
            "Where should the data land? (e.g. BigQuery, Snowflake, S3)",
            "Destination determines load strategy and schema mapping.",
            None,
        ),
    ],
    "scheduling": [
        (
            "attendees",
            "Who needs to attend the meeting?",
            "Attendee list is required for availability checking.",
            None,
        ),
        (
            "duration",
            "How long should the meeting be?",
            "Duration determines slot-search parameters.",
            ["30 minutes", "1 hour", "90 minutes", "2 hours"],
        ),
    ],
    "procurement": [
        (
            "item",
            "What item or service do you need to procure?",
            "Item specification is needed for vendor matching.",
            None,
        ),
        (
            "quantity",
            "How many units are required?",
            "Quantity affects bulk-pricing and vendor selection.",
            None,
        ),
    ],
}

# Generic question for fully unknown domain
_GENERIC_QUESTION = ClarificationQuestion(
    question="Could you describe what you'd like to accomplish in a bit more detail?",
    reason="The request wasn't specific enough to determine the right workflow.",
    options=None,
    field="raw_input",
)


class ClarificationEngine:
    """Generate the minimum set of ClarificationQuestions for a UserIntent."""

    def needs_clarification(self, intent: UserIntent) -> bool:
        """Return True if any clarification would be generated."""
        return bool(self.generate(intent))

    def generate(self, intent: UserIntent) -> list[ClarificationQuestion]:
        """Return questions needed to resolve the intent.

        Returns an empty list when the intent is clear enough to proceed.
        """
        # Unknown domain — one generic question only
        if intent.inferred_domain is None:
            if intent.ambiguity_score > AMBIGUITY_THRESHOLD:
                return [_GENERIC_QUESTION]
            return []

        template = get_template(intent.inferred_domain)
        questions = self._domain_questions(intent, template)

        # Also trigger if highly ambiguous even after domain is known
        if not questions and intent.ambiguity_score > AMBIGUITY_THRESHOLD:
            q = self._fallback_question(intent)
            if q:
                questions.append(q)

        return questions

    # ── Domain-specific question generation ──────────────────────────

    def _domain_questions(
        self,
        intent: UserIntent,
        template: WorkflowTemplate | None,
    ) -> list[ClarificationQuestion]:
        domain = intent.inferred_domain or ""
        domain_defs = _DOMAIN_QUESTIONS.get(domain, [])
        questions: list[ClarificationQuestion] = []

        for field, question_text, reason, options in domain_defs:
            if self._field_present(field, intent):
                continue
            questions.append(
                ClarificationQuestion(
                    question=question_text,
                    reason=reason,
                    options=options,
                    field=field,
                )
            )

        return questions

    def _field_present(self, field: str, intent: UserIntent) -> bool:
        """Return True if the given field is already populated in the intent."""
        if field in intent.constraints and intent.constraints[field] is not None:
            return True
        if field in intent.preferences and intent.preferences[field]:
            return True
        # Destination / named entities
        if field == "destination":
            return bool(intent.extracted_entities)
        # Free-text fields stored in constraints under same name
        if field == "incident_description":
            # If the raw input is longer than ~10 words it probably has a description
            return len(intent.raw_input.split()) >= 10
        if field == "severity":
            raw = intent.raw_input.lower()
            return any(s in raw for s in ("p0", "p1", "p2", "p3", "critical", "high", "medium"))
        if field == "source":
            return "source" in intent.constraints
        if field == "attendees":
            return "attendees" in intent.constraints
        return False

    def _fallback_question(self, intent: UserIntent) -> ClarificationQuestion | None:
        """A soft catch-all question for ambiguous-but-domain-known requests."""
        domain = intent.inferred_domain or ""
        labels = {
            "business_travel": (
                "Any other details about your trip? (dates, preferences, etc.)",
                "destination",
            ),
            "incident_response": (
                "Any additional details about the incident?",
                "incident_description",
            ),
            "data_pipeline": ("Any specific requirements for the pipeline?", "requirements"),
            "scheduling": ("Any preferences for meeting time or format?", "preferences"),
            "procurement": ("Any vendor preferences or quality requirements?", "requirements"),
        }
        if domain in labels:
            text, field = labels[domain]
            return ClarificationQuestion(question=text, reason="Ambiguous input.", options=None, field=field)
        return None
