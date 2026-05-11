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
* Experience abstraction layer
* Intent interpretation
* Workflow synthesis
* Constraint negotiation
* Operational steering
* Preference memory
* Proactive optimization
* Human-readable workflow progress
* Narrative summaries
* Deterministic and Cognitive planning modes

The architecture is stable and modular.

Your task is to implement:

# Human Operational Guidance (Advanced HITL)

IMPORTANT:
This is NOT chatbot functionality.

This is:

* governed human operational steering
* bounded runtime guidance injection
* collaborative workflow adaptation
* operationally scoped human input

The goal is:

Freya should no longer support ONLY:

* Approve
* Reject

Instead:
users should be able to provide:

* operational guidance
* constraint modifications
* preference adjustments
* steering instructions
* execution priorities

DURING workflow execution.

WITHOUT:

* breaking workflow safety
* bypassing governance
* becoming a freeform chatbot
* creating uncontrolled autonomy

This is:

* collaborative governed execution
  NOT:
* conversational AI.

---

# PRIMARY DESIGN GOAL

Current behavior:

Freya:
"Premium hotel exceeds budget.
Approve?"

User:
Approve / Reject

NEW behavior:

Freya:
"Premium hotel exceeds budget.
Approve?"

User:
"Find something slightly cheaper closer to the metro."

Freya:
"Updated hotel search strategy.
Reassessing travel plan..."

This should feel:

* collaborative
* operational
* intelligent
* bounded
* governed

NOT:

* chatbot-like
* uncontrolled
* conversationally open-ended

---

# CREATE NEW MODULE STRUCTURE

Create:

freya/hitl/
**init**.py

freya/hitl/models.py
freya/hitl/guidance.py
freya/hitl/interpreter.py
freya/hitl/applier.py
freya/hitl/governance.py
freya/hitl/rendering.py
freya/hitl/cli.py

Create a NEW example file:

examples/hitl_guidance_demo.py

DO NOT modify previous demos.

---

# REQUIREMENTS

# 1. Add HITL Guidance Models

Create:

freya/hitl/models.py

Define:

HumanGuidance

* guidance_id: str
* raw_input: str
* interpreted_intent: str
* guidance_type: str
* extracted_constraints: dict
* extracted_preferences: dict
* confidence_score: float
* requires_governance_review: bool

GuidanceApplicationResult

* success: bool
* applied_changes: list[str]
* workflow_updates: list[str]
* governance_actions: list[str]
* narrative_summary: str

GuidanceGovernanceDecision

* allowed: bool
* reason: str
* requires_approval: bool

Use Pydantic v2.

---

# 2. Add Human Guidance Interpreter

Create:

freya/hitl/interpreter.py

Implement:

HumanGuidanceInterpreter

Responsibilities:

* parse operational guidance
* extract steering intent
* extract constraint changes
* identify preference changes
* classify guidance type

Supported guidance types:

* cost_adjustment
* priority_change
* preference_update
* governance_override_request
* optimization_request
* execution_depth_change
* recovery_policy_change

Examples:

"Find something cheaper"
→ cost_adjustment

"Prioritize convenience"
→ priority_change

"Skip deep comparison"
→ execution_depth_change

Use REAL LLM parsing if available.

Fallback:
deterministic parsing heuristics.

---

# 3. Add Guidance Application Engine

Create:

freya/hitl/applier.py

Implement:

HumanGuidanceApplier

Responsibilities:

* safely modify workflow state
* update steering constraints
* update optimization priorities
* update execution preferences
* trigger reassessment

Guidance should:

* modify workflows safely
* preserve persistence
* preserve governance
* preserve auditability

DO NOT:

* restart workflows unnecessarily
* silently mutate workflows
* bypass governance

---

# 4. Add HITL Governance Layer

Create:

freya/hitl/governance.py

Implement:

HumanGuidanceGovernance

Responsibilities:

* validate guidance safety
* prevent governance bypass
* review risky guidance
* require escalation where necessary

Examples:

* disabling governance requires approval
* removing approval checks blocked
* aggressive optimization requires review

All human guidance must remain:

* governed
* auditable
* bounded
* explainable

---

# 5. Add Human-Centered Rendering

Create:

freya/hitl/rendering.py

Implement:

render_guidance_prompt(...)
render_guidance_result(...)
render_guidance_review(...)

Rendering must feel:

* operational
* concise
* executive-friendly

NOT:

* chatbot-like
* verbose AI dialogue

Example:

## Operational Guidance

The selected hotel exceeds your preferred budget.

You may:

* approve
* reject
* provide revised guidance

Example guidance:

* "Find something cheaper"
* "Prioritize convenience"
* "Avoid premium hotels"

---

# 6. Add CLI Interaction Layer

Create:

freya/hitl/cli.py

IMPORTANT:
Build a PROPER terminal interaction layer.

This is VERY important.

The CLI should feel:

* professional
* workflow-oriented
* operational
* interactive

NOT:

* like raw input() prompts
* like a chatbot terminal

Use:

* structured prompts
* numbered choices
* guidance input sections
* workflow status sections
* approval review sections

CLI capabilities:

* approve
* reject
* enter operational guidance
* inspect current workflow state
* inspect optimization proposals
* continue execution safely

Example interaction:

==================================================
Approval Required — Premium Hotel Selection
===========================================

Reason:
Selected hotel exceeds preferred budget by ₹8,000.

Current Recommendation:
Business hotel near client office.

Options:
[1] Approve
[2] Reject
[3] Provide Guidance
[4] View Optimization Details

Select option: 3

Enter operational guidance:

> Find something slightly cheaper closer to metro access.

Processing guidance...
Updated workflow strategy:

* prioritize metro proximity
* reduce hotel budget target
* reassess optimization proposals

Workflow resumed successfully.

The CLI should support:

* progressive disclosure
* operational summaries
* concise workflow updates

DO NOT:

* build chatbot terminal UX
* build freeform conversation loops

---

# 7. Add Runtime Integration

Integrate HITL guidance with:

* steering layer
* optimization layer
* governance layer
* experience layer
* preference memory
* workflow synthesis
* economics layer

Guidance should affect:

* optimization opportunities
* workflow priorities
* execution strategies
* governance behavior
* runtime adaptation

---

# 8. Add Auditability

VERY IMPORTANT.

All guidance must be:

* persisted
* traceable
* auditable
* reviewable

Add:

* guidance history
* workflow guidance timeline
* governance review trace

This is critical for enterprise use.

---

# 9. Add Continuous Reassessment

When guidance is applied:
Freya should:

* reassess workflow state
* reassess optimization opportunities
* reassess economics
* reassess governance impact

WITHOUT:

* full workflow restart
* unnecessary replanning

---

# 10. Add NEW Example File

Create:

examples/hitl_guidance_demo.py

Demonstrate:

### Scenario BI — Guidance Instead of Approval

* user provides revised operational guidance

### Scenario BJ — Steering Integration

* guidance updates workflow priorities

### Scenario BK — Optimization Reassessment

* optimization changes after guidance

### Scenario BL — Governance Review

* risky guidance requires governance review

### Scenario BM — CLI Workflow Interaction

* professional interactive CLI experience

### Scenario BN — Guidance Audit Trail

* guidance history rendered

The demo should feel:

* collaborative
* operational
* intelligent
* enterprise-grade

NOT:

* chatbot-like
* conversationally chaotic

---

# 11. HARD RULES

DO NOT:

* build open-ended chat systems
* build AI personalities
* create unrestricted prompting
* bypass governance
* expose raw runtime internals
* create conversational agent loops

This is:

* governed operational collaboration
  NOT:
* chatbot interaction.

---

# 12. DESIGN INTENT

This step transitions Freya from:

* approval-gated workflows

to:

* collaboratively steerable governed execution

Freya should now feel:

* adaptive
* steerable
* operationally collaborative
* intelligently bounded

WITHOUT:

* losing governance
* losing auditability
* losing predictability
* becoming autonomous chaos

The system should feel like:

"an intelligent operational coordination platform"

NOT:

"a chatbot agent."

---

# OUTPUT FORMAT

Provide:

1. HITL modules
2. Human guidance interpreter
3. Guidance application engine
4. Governance validation layer
5. Human-centered rendering
6. Professional CLI interaction layer
7. Runtime integration
8. Auditability support
9. NEW example:
   examples/hitl_guidance_demo.py

Do NOT explain.
Only output code.
