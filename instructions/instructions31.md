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
* Multi-workflow coordination
* Delegation contracts
* Adaptive execution strategies
* Execution economics
* Resource governance
* Experience abstraction layer
* Human-readable workflow progress
* Narrative summaries
* Intent interpretation
* Workflow synthesis
* Clarification handling
* Progressive disclosure rendering
* Deterministic and Cognitive planning modes

The architecture is stable and modular.

Your task is to implement:

# Constraint Negotiation + Operational Steering Layer

IMPORTANT:
This is NOT chatbot behavior.

This is:

* operational collaboration
* tradeoff negotiation
* adaptive workflow steering
* constraint-aware execution guidance

The goal is:

Freya should no longer feel:

* scripted
* template-driven
* request/response only

Instead:
Freya should feel like:

* an intelligent operational coordinator
* capable of negotiating tradeoffs
* capable of adapting workflows during execution

WITHOUT:

* becoming an open-ended conversational agent
* becoming a personality-driven chatbot
* exposing runtime internals

This is:

* governed operational interaction
  NOT:
* AI companionship.

---

# PRIMARY DESIGN GOAL

Current behavior:

User:
"Plan a Bangalore trip under ₹40k"

Freya:
"Here is the synthesized workflow."

NEW behavior:

Freya should ALSO be capable of:

"Hotels near the venue exceed your budget.
Would you like to:

* increase budget
* stay farther away
* reduce hotel quality"

This is:

* operational steering
* constraint negotiation
* adaptive collaboration

---

# CREATE NEW MODULE STRUCTURE

Create:

freya/steering/
**init**.py

freya/steering/models.py
freya/steering/negotiation.py
freya/steering/decisioning.py
freya/steering/preferences.py
freya/steering/recommendations.py
freya/steering/rendering.py

Create a NEW example file:

examples/operational_steering_demo.py

DO NOT modify previous demos.

---

# REQUIREMENTS

# 1. Add Steering Models

Create:

freya/steering/models.py

Define:

OperationalConstraint

* name: str
* value: str | int | float | bool
* priority: str
* negotiable: bool

NegotiationOption

* option_id: str
* title: str
* description: str
* impact_summary: str
* estimated_cost_change: float | None
* estimated_time_change: float | None

NegotiationProposal

* reason: str
* detected_conflict: str
* options: list[NegotiationOption]

OperationalPreference

* preference_name: str
* preference_value: str
* confidence: float

Use Pydantic v2.

---

# 2. Add Constraint Negotiation Engine

Create:

freya/steering/negotiation.py

Implement:

ConstraintNegotiationEngine

Responsibilities:

* detect workflow conflicts
* detect impossible constraints
* detect tradeoff opportunities
* generate negotiation proposals

Examples:

* hotel proximity conflicts with budget
* premium flight conflicts with timeline
* fast execution conflicts with deep analysis

This is VERY important.

The system should proactively negotiate constraints.

NOT fail silently.

---

# 3. Add Operational Steering Decisions

Create:

freya/steering/decisioning.py

Implement:

OperationalSteeringEngine

Responsibilities:

* dynamically steer workflows
* update workflow priorities
* modify execution constraints
* apply user decisions

Examples:

* reduce costs
* prioritize speed
* prioritize quality
* avoid premium upgrades
* minimize approvals

This becomes:

* runtime operational steering.

---

# 4. Add Preference Learning Layer

Create:

freya/steering/preferences.py

Implement:

PreferenceMemory

Responsibilities:

* remember user operational preferences
* store prior negotiation outcomes
* infer preference tendencies

Examples:

* prefers lower cost
* prefers proximity
* usually approves premium upgrades
* prioritizes speed over deep analysis

Persistence should be lightweight/local for now.

DO NOT build:

* vector databases
* embeddings
* long-term memory systems

Keep it deterministic/simple.

---

# 5. Add Recommendation Engine

Create:

freya/steering/recommendations.py

Implement:

OperationalRecommendationEngine

Responsibilities:

* recommend better tradeoffs
* summarize operational impacts
* proactively suggest optimizations

Examples:

"Upgrading the hotel by ₹5,000 reduces commute time by ~2 hours/day."

"Skipping deep comparison reduces planning time significantly."

This is CRITICAL.

The system should feel:

* operationally intelligent
  NOT:
* reactive only.

---

# 6. Add Human-Centered Rendering

Create:

freya/steering/rendering.py

Implement:

render_negotiation(...)
render_recommendation(...)
render_operational_update(...)

The rendering must feel:

* concise
* operational
* business-oriented

NOT:

* verbose AI chat.

Example:

## Tradeoff Detected

Hotels near the client office exceed your preferred budget.

Available Options:

1. Increase hotel budget by ₹8,000
2. Stay farther from venue
3. Reduce hotel quality

Recommended:
Option 1 — saves ~2 hours/day commute time.

---

# 7. Add Runtime Steering Integration

Integrate with:

* experience layer
* economics layer
* governance layer
* adaptive execution strategies

Steering decisions should affect:

* workflow synthesis
* strategy escalation
* governance requirements
* execution economics

Example:
"Prioritize speed"
→ reduce cognitive analysis
→ reduce cost
→ reduce deep comparisons

---

# 8. Add Dynamic Workflow Modification

VERY IMPORTANT.

Workflows should become dynamically steerable.

Example:
User changes:

* budget
* urgency
* quality preference
* execution depth

during execution.

The workflow should adapt safely.

WITHOUT:

* restarting from scratch.

---

# 9. Add Operational Collaboration UX

The interaction model should feel like:

Freya:
"Premium hotels exceed your preferred budget.
Would you like to optimize for convenience or lower cost?"

User:
"Lower cost."

Freya:
"Understood. Prioritizing budget-friendly hotels."

This is:

* bounded collaboration
  NOT:
* chatbot conversation.

---

# 10. Add NEW Example File

Create:

examples/operational_steering_demo.py

Demonstrate:

### Scenario AV — Budget vs Convenience Negotiation

* detect conflict
* generate negotiation options

### Scenario AW — Runtime Steering

* user changes priority during execution
* workflow adapts safely

### Scenario AX — Recommendation Engine

* proactive optimization recommendation

### Scenario AY — Preference Memory

* system remembers prior preference tendencies

### Scenario AZ — Economics + Steering Integration

* steering changes execution economics

### Scenario BA — Governance-Aware Steering

* steering change triggers governance review

The demo should feel:

* adaptive
* collaborative
* operational
* intelligent

NOT:

* scripted
* chatbot-like

---

# 11. HARD RULES

DO NOT:

* create open-ended chat loops
* create personalities
* create agent roleplay
* expose runtime internals
* expose orchestration semantics
* build general chat interfaces

This is:

* operational collaboration
  NOT:
* conversational AI.

---

# 12. DESIGN INTENT

This step transitions Freya from:

* intent-driven orchestration

to:

* adaptive operational collaboration

Freya should now feel like:

* an operational coordinator
* capable of negotiating tradeoffs
* capable of adapting execution
* capable of steering workflows safely

WITHOUT:

* losing governance
* losing bounded execution
* becoming an uncontrolled agent

The system should feel:

"collaborative and operationally intelligent"

NOT:

"chatbot-like."

---

# OUTPUT FORMAT

Provide:

1. Steering layer modules
2. Constraint negotiation engine
3. Operational steering engine
4. Preference memory
5. Recommendation engine
6. Human-centered rendering
7. Runtime steering integration
8. NEW example:
   examples/operational_steering_demo.py

Do NOT explain.
Only output code.
