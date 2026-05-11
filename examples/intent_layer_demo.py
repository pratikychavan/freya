"""examples/intent_layer_demo.py

Intent Interpretation + Workflow Synthesis Layer — Demo
=======================================================

Scenarios:
  AQ — Clear Intent         : business travel → direct blueprint synthesis
  AR — Ambiguous Intent     : vague request → clarification questions
  AS — Blueprint Rendering  : rich terminal rendering of a workflow blueprint
  AT — Constraint Extraction: shows how budget, nights, preferences are parsed
  AU — Intent → Experience  : synthesized goal feeds the experience layer

Run with:
    python examples/intent_layer_demo.py
"""
from __future__ import annotations

import asyncio
import textwrap

# ---------------------------------------------------------------------------
# Intent layer
# ---------------------------------------------------------------------------
from freya.intent import (
    IntentPipeline,
    render_clarification_questions,
    render_intent_summary,
    render_parse_result,
    render_workflow_blueprint,
)
from freya.intent.classifier import IntentClassifier

# ---------------------------------------------------------------------------
# Experience layer (for AU)
# ---------------------------------------------------------------------------
from freya.experience import (
    WorkflowProgressTracker,
    render_user_view,
)

# ── ANSI helpers ─────────────────────────────────────────────────────
_BOLD = "\033[1m"
_DIM = "\033[2m"
_CYAN = "\033[96m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RESET = "\033[0m"


def _section(label: str) -> None:
    width = 70
    print()
    print(f"{_CYAN}{'═' * width}{_RESET}")
    print(f"{_BOLD}  {label}{_RESET}")
    print(f"{_CYAN}{'═' * width}{_RESET}")


def _user_says(text: str) -> None:
    print(f"\n  {_DIM}User:{_RESET} {_YELLOW}\"{text}\"{_RESET}\n")


# ---------------------------------------------------------------------------
# Scenario AQ — Clear Intent
# ---------------------------------------------------------------------------
async def scenario_aq() -> None:
    _section("Scenario AQ — Clear Intent: Business Travel")

    utterance = "Plan my trip to Bangalore for 2 nights, budget ₹40,000. I need a hotel near the client office."
    _user_says(utterance)

    pipeline = IntentPipeline()
    result = await pipeline.process(utterance)

    print(render_parse_result(result))

    if result.ready_to_execute:
        print(f"\n  {_GREEN}✓ Intent resolved — ready to orchestrate workflow.{_RESET}")
        print(f"  Synthesized Goal: {_BOLD}{result.blueprint.synthesized_goal}{_RESET}")
    else:
        print(f"\n  Clarification needed before proceeding.")


# ---------------------------------------------------------------------------
# Scenario AR — Ambiguous Intent
# ---------------------------------------------------------------------------
async def scenario_ar() -> None:
    _section("Scenario AR — Ambiguous Intent: Clarification Triggered")

    utterance = "Book a hotel"
    _user_says(utterance)

    pipeline = IntentPipeline()
    result = await pipeline.process(utterance)

    print(render_intent_summary(result.intent, title="Partial Intent Captured"))
    print()

    if result.clarifications:
        print(render_clarification_questions(result.clarifications))
        print(f"\n  {_YELLOW}⚠  Workflow synthesis paused — waiting for answers.{_RESET}")
    else:
        print(render_parse_result(result))


# ---------------------------------------------------------------------------
# Scenario AS — Blueprint Rendering
# ---------------------------------------------------------------------------
async def scenario_as() -> None:
    _section("Scenario AS — Workflow Blueprint Rendering")

    utterance = "Coordinate the Bangalore tech summit trip, 3 nights, ₹75,000 budget, prefer business class."
    _user_says(utterance)

    pipeline = IntentPipeline()
    result = await pipeline.process(utterance)

    if result.blueprint:
        print(render_workflow_blueprint(result.blueprint))
        print()
        print(f"  {_DIM}Template ID: {result.blueprint.template_id}{_RESET}")
        print(f"  {_DIM}Strategy:    {result.blueprint.recommended_strategy}{_RESET}")
        print(f"  {_DIM}Complexity:  {result.blueprint.estimated_complexity}{_RESET}")
    else:
        print(render_clarification_questions(result.clarifications))


# ---------------------------------------------------------------------------
# Scenario AT — Constraint Extraction
# ---------------------------------------------------------------------------
async def scenario_at() -> None:
    _section("Scenario AT — Constraint Extraction")

    utterances = [
        "Book flights to Mumbai, ₹15,000 budget, 1 night stay",
        "I need to go to Delhi for a vendor meeting, under Rs 25,000, near Connaught Place",
        "Plan a premium 4-night Hyderabad trip for the leadership summit, budget ₹1,20,000",
    ]

    classifier = IntentClassifier()
    pipeline = IntentPipeline()

    for utt in utterances:
        _user_says(utt)
        domain, confidence = classifier.classify(utt)
        result = await pipeline.process(utt)
        intent = result.intent

        print(f"  Domain     : {(domain or 'Unknown').replace('_', ' ').title()}  (confidence {confidence:.0%})")
        print(f"  Primary Goal: {intent.primary_goal}")
        if intent.constraints:
            print("  Constraints :")
            for k, v in intent.constraints.items():
                label = k.replace("_", " ").title()
                if k == "budget_inr" and isinstance(v, (int, float)):
                    v = f"₹{int(v):,}"
                print(f"    • {label}: {v}")
        if intent.preferences:
            print("  Preferences :")
            for k in intent.preferences:
                print(f"    • {k.replace('_', ' ').title()}")
        if intent.extracted_entities:
            print(f"  Entities    : {', '.join(intent.extracted_entities)}")
        print()


# ---------------------------------------------------------------------------
# Scenario AU — Intent → Experience Integration
# ---------------------------------------------------------------------------
async def scenario_au() -> None:
    _section("Scenario AU — Intent → Experience Layer Integration")

    utterance = "Arrange my Pune client visit — 2 nights, ₹35,000 total"
    _user_says(utterance)

    # 1. Parse intent
    pipeline = IntentPipeline()
    result = await pipeline.process(utterance)

    if not result.ready_to_execute or not result.blueprint:
        print("  Intent unclear — showing clarification questions.")
        print(render_clarification_questions(result.clarifications))
        return

    blueprint = result.blueprint
    print(render_workflow_blueprint(blueprint))
    print()

    # 2. Simulate workflow execution using the experience layer's tracker
    print(f"  {_DIM}Simulating workflow execution...{_RESET}\n")

    tracker = WorkflowProgressTracker()
    # Simulate events: flights searched, hotels found, now comparing
    fake_events = [
        {"event_type": "tool_call_completed", "payload": {"tool_name": "search_primary_flights"}},
        {"event_type": "tool_call_completed", "payload": {"tool_name": "search_hotels"}},
    ]
    tracker.from_events(fake_events)

    print(render_user_view(goal=blueprint.synthesized_goal, tracker=tracker))
    print()

    # 3. Show synthesized goal that would be passed to the runner
    print(f"  {_BOLD}Synthesized Goal (for runner.run()){_RESET}")
    wrapped = textwrap.fill(blueprint.synthesized_goal, width=60, initial_indent="  → ", subsequent_indent="    ")
    print(wrapped)
    print()
    print(f"  {_GREEN}✓ Intent successfully bridged to the experience layer.{_RESET}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
async def main() -> None:
    print(f"\n{_BOLD}{_CYAN}  Freya — Intent Interpretation + Workflow Synthesis{_RESET}")
    print(f"  {'─' * 50}")

    await scenario_aq()
    await scenario_ar()
    await scenario_as()
    await scenario_at()
    await scenario_au()

    print(f"\n{_DIM}  Demo complete.{_RESET}\n")


if __name__ == "__main__":
    asyncio.run(main())
