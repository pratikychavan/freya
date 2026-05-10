You are working inside the Freya SDK repository.

Freya already supports:

* ExecutionEngine
* DAGRunner
* IterativePlannerRunner
* GovernanceEngine
* Approval checkpoints
* Durable workflow persistence
* WorkflowSnapshot
* Workflow versioning
* Workflow leases
* Event-driven runtime
* RuntimeEvent
* Event subscribers
* Multi-workflow coordination
* Delegation contracts
* Adaptive execution strategies
* Execution economics
* Resource governance
* Strategy persistence
* Workflow trees
* Deterministic and Cognitive planning modes

The architecture is stable and modular.

Your task is to implement:

# Experience Abstraction Layer (P0 UX)

IMPORTANT:
This is NOT frontend UI work.

This is:

* human interaction abstraction
* experience orchestration
* runtime-to-human translation

The goal is:

Hide orchestration complexity from normal users.

Freya currently exposes:

* runtime semantics
* workflow internals
* governance mechanics
* strategy terminology
* event terminology

This is excellent for engineers,
but terrible for end-user usability.

Now Freya must support:

* human-readable workflow progress
* approval explanations
* narrative summaries
* intent-friendly interaction
* progressive disclosure

WITHOUT:

* removing observability
* removing governance
* removing traces
* removing execution correctness

This is:

* abstraction
  NOT:
* simplification of runtime.

---

# PRIMARY DESIGN GOAL

Normal users should see:

"Planning your business trip..."

NOT:

"execution_strategy_selected"

---

# CREATE NEW MODULE STRUCTURE

Create:

freya/experience/
**init**.py

freya/experience/models.py
freya/experience/progress.py
freya/experience/approval.py
freya/experience/narrative.py
freya/experience/rendering.py
freya/experience/translators.py

Create a NEW example file:

examples/experience_layer_demo.py

DO NOT modify previous demos.

---

# REQUIREMENTS

# 1. Add Human Experience Models

Create:

freya/experience/models.py

Define:

HumanProgressUpdate

* title: str
* status: str
* detail: str | None
* timestamp: datetime

ApprovalExperience

* title: str
* message: str
* impact_summary: str
* choices: list[str]

NarrativeSummary

* title: str
* summary: str
* highlights: list[str]

Use Pydantic v2.

---

# 2. Add Runtime Event Translation Layer

Create:

freya/experience/translators.py

Implement:

RuntimeEventTranslator

Responsibilities:

* convert RuntimeEvents → HumanProgressUpdate
* hide runtime terminology
* produce human-readable progress

Examples:

Internal event:
workflow_paused_for_approval

Human output:
"Waiting for your approval..."

Internal event:
subworkflow_spawned

Human output:
"Searching hotel options..."

Internal event:
execution_strategy_selected (cognitive)

Human output:
"Optimizing travel plan..."

Internal event:
runtime_failure_observed

Human output:
"Encountered temporary issue. Retrying..."

---

# 3. Add Approval Experience Layer

Create:

freya/experience/approval.py

Implement:

ApprovalExperienceBuilder

Responsibilities:

* convert governance approvals into business-language explanations
* explain impact
* present simple choices

Example:

NOT:
"HighCostApprovalPolicy triggered"

INSTEAD:
"The selected hotel exceeds your preferred budget by ₹8,000."

Choices:

* Approve
* Reject

---

# 4. Add Narrative Summary Layer

Create:

freya/experience/narrative.py

Implement:

NarrativeSummaryGenerator

Responsibilities:

* generate human-readable workflow summaries
* explain workflow outcomes
* summarize adaptations/recoveries

Use REAL LLM summarization if available.

Fallback:
deterministic summary rendering.

Example output:

"Your Bangalore trip was successfully planned.

* Selected flights within budget
* Chose hotel near client office
* Recovered from temporary flight provider issue
* Total estimated trip cost: ₹36,500"

DO NOT expose:

* raw traces
* strategies
* contracts
* governance internals

---

# 5. Add Progressive Disclosure Rendering

Create:

freya/experience/rendering.py

Implement:

render_user_view(...)
render_power_user_view(...)
render_engineer_view(...)

Behavior:

USER VIEW:

* progress only
* approvals
* summaries

POWER USER VIEW:

* economics
* workflow summaries
* high-level strategy changes

ENGINEER VIEW:

* raw events
* strategies
* contracts
* traces
* governance internals

This is CRITICAL.

DO NOT remove observability.

Instead:
layer visibility.

---

# 6. Add Experience Event Mapping Registry

Implement configurable event mappings.

Example:

EVENT_TRANSLATIONS = {
"workflow_paused_for_approval":
"Waiting for your approval...",
}

Avoid hardcoded giant if/else chains.

---

# 7. Add Human-Friendly Workflow Progress

Render workflow lifecycle as:

✓ Searching flights
✓ Comparing hotels
⚠ Approval required
✓ Optimizing itinerary
✓ Recovering from provider issue
✓ Trip finalized

NOT:

* raw runtime events
* workflow DAGs
* strategy internals

---

# 8. Add Approval Narratives

Approvals should include:

* why approval needed
* business impact
* budget impact
* user-facing explanation

Example:

## Approval Required

The recommended hotel exceeds your preferred budget by ₹8,000,
but is significantly closer to the client office.

Impact:

* Lower travel time
* Better meeting convenience
* Slightly higher cost

Choices:
[Approve] [Reject]

---

# 9. Add Experience Session Continuity

Add simple human-readable session state rendering.

Examples:

"Trip planning paused awaiting approval."

"Trip planning resumed successfully."

"Workflow restored from saved progress."

This builds:

* trust
* continuity
* confidence

---

# 10. Add NEW Example File

Create:

examples/experience_layer_demo.py

Demonstrate:

### Scenario AL — User-Friendly Progress

* runtime events translated into human progress

### Scenario AM — Approval Experience

* governance approval rendered naturally

### Scenario AN — Narrative Summary

* workflow summarized naturally

### Scenario AO — Progressive Disclosure

Render:

* user view
* power-user view
* engineer view

### Scenario AP — Session Continuity

* pause workflow
* restore workflow
* human-readable lifecycle updates

The example output should feel:

* polished
* human-centered
* product-like

NOT:

* engineering logs

---

# 11. HARD RULES

DO NOT:

* remove runtime observability
* remove governance visibility
* remove debugging detail
* create fake orchestration
* create chat interfaces
* expose raw runtime internals to user view

This is:

* abstraction
  NOT:
* removal of engineering detail.

---

# 12. DESIGN INTENT

This step transitions Freya from:

* runtime-centric interaction

to:

* human-centered governed orchestration experience

The system should feel like:

"an intelligent operations coordinator"

NOT:
"a workflow engine."

Users should experience:

* intent
* progress
* approvals
* outcomes

NOT:

* runtime mechanics

---

# OUTPUT FORMAT

Provide:

1. Experience layer modules
2. Runtime event translator
3. Approval experience builder
4. Narrative summary generator
5. Progressive disclosure rendering
6. Human-readable workflow rendering
7. NEW example:
   examples/experience_layer_demo.py

Do NOT explain.
Only output code.
