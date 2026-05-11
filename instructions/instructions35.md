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
* Proactive optimization
* Human operational guidance (HITL)
* Semantic governance intent classification
* Guidance audit trails
* Interactive operational CLI
* Deterministic and Cognitive planning modes

The architecture is stable and modular.

Your task is to implement:

# Contextual Operational Cognition Layer

IMPORTANT:
This is NOT chatbot memory.

This is:

* workflow-context awareness
* operational situational cognition
* governance-aware contextual reasoning
* execution-history-aware interpretation

The goal is:

Freya should no longer interpret:

* guidance
* steering
* optimization requests
* approvals
* tradeoffs

ONLY from:

* the current message

Instead:
Freya should interpret them using:

* workflow history
* prior guidance
* optimization trajectory
* governance history
* operational state
* user operational tendencies

This is:

* contextual operational cognition
  NOT:
* conversational memory.

---

# PRIMARY DESIGN GOAL

Current behavior:

User:
"Make it cheaper."

Freya:
Interprets using only the current message.

NEW behavior:

Freya understands:

* current workflow already optimized twice
* user previously prioritized metro access
* governance denied premium bypass earlier
* workflow currently in cost-sensitive mode

Then:
interpret guidance CONTEXTUALLY.

This should feel:

* situationally aware
* operationally intelligent
* context-sensitive
* governed

NOT:

* chatbot-like
* stateless
* prompt-reactive

---

# CREATE NEW MODULE STRUCTURE

Create:

freya/context/
**init**.py

freya/context/models.py
freya/context/store.py
freya/context/history.py
freya/context/cognition.py
freya/context/governance.py
freya/context/trajectory.py
freya/context/preferences.py
freya/context/rendering.py

Create a NEW example file:

examples/contextual_operational_cognition_demo.py

DO NOT modify previous demos.

---

# REQUIREMENTS

# 1. Add Context Models

Create:

freya/context/models.py

Define:

OperationalContext

* workflow_id: str
* workflow_state: str
* active_constraints: dict
* active_preferences: dict
* optimization_history: list[str]
* governance_history: list[str]
* prior_guidance: list[str]
* operational_mode: str
* execution_strategy: str

ContextualInterpretation

* raw_input: str
* interpreted_meaning: str
* contextual_reasoning: list[str]
* inferred_operational_intent: str
* confidence_score: float
* contextual_risk: str

OperationalTrajectory

* trajectory_id: str
* prior_decisions: list[str]
* optimization_direction: str
* governance_pattern: str
* execution_drift: str | None

Use Pydantic v2.

---

# 2. Add Context Store

Create:

freya/context/store.py

Implement:

OperationalContextStore

Responsibilities:

* persist operational context
* persist workflow trajectory
* store guidance history
* store optimization history
* store governance outcomes

Requirements:

* lightweight deterministic persistence
* session-scoped context
* resumable context state

DO NOT:

* build vector databases
* build embeddings
* build chatbot memory

Keep:

* operational
* structured
* auditable

---

# 3. Add Workflow History Engine

Create:

freya/context/history.py

Implement:

WorkflowHistoryEngine

Responsibilities:

* summarize workflow evolution
* summarize prior guidance
* summarize optimization changes
* summarize governance outcomes

Examples:

* "User consistently prioritized convenience."
* "Workflow optimized for lower cost twice."
* "Governance denied approval bypass request."

This history should become:

* operational context input
* steering context
* optimization context

---

# 4. Add Contextual Cognition Engine

Create:

freya/context/cognition.py

Implement:

ContextualOperationalCognitionEngine

Responsibilities:

* interpret guidance using workflow context
* interpret operational meaning contextually
* infer situational intent
* reason about operational trajectory

Examples:

Input:
"Make it cheaper."

WITHOUT context:
→ generic cost reduction

WITH context:
→ reduce hotel quality but preserve metro proximity
because prior guidance prioritized location.

This is VERY important.

The engine should:

* understand workflow evolution
* understand operational state
* understand optimization direction

WITHOUT:

* becoming a general conversational AI.

---

# 5. Add Contextual Governance Layer

Create:

freya/context/governance.py

Implement:

ContextualGovernanceEngine

Responsibilities:

* apply governance contextually
* evaluate operational history
* detect risky behavioral patterns
* adjust governance strictness

Examples:

* repeated bypass attempts increase scrutiny
* repeated risky optimizations require escalation
* trusted workflow patterns reduce friction

Governance should become:

* situationally aware
  NOT:
* purely static.

---

# 6. Add Operational Trajectory Engine

Create:

freya/context/trajectory.py

Implement:

OperationalTrajectoryEngine

Responsibilities:

* track workflow evolution
* track optimization direction
* detect execution drift
* detect operational instability

Examples:

* workflow repeatedly changing priorities
* escalating governance conflicts
* optimization oscillation
* increasing execution cost drift

This becomes:

* operational situational awareness.

---

# 7. Add Contextual Preference Engine

Create:

freya/context/preferences.py

Implement:

ContextualPreferenceEngine

Responsibilities:

* infer operational tendencies
* infer recurring steering behavior
* infer optimization preferences
* infer governance comfort level

Examples:

* repeatedly prioritizes speed
* avoids deep analysis
* consistently accepts premium upgrades
* prefers lower governance friction

This is:

* operational preference cognition
  NOT:
* personality profiling.

---

# 8. Add Human-Centered Rendering

Create:

freya/context/rendering.py

Implement:

render_operational_context(...)
render_contextual_reasoning(...)
render_operational_trajectory(...)

Rendering should feel:

* operational
* situationally aware
* executive-friendly

NOT:

* verbose reasoning dumps
* chain-of-thought exposure
* chatbot memory rendering

Example:

## Operational Context

Current Workflow Mode:
Cost-sensitive planning

Recent Guidance:

* prioritize metro access
* reduce hotel budget
* avoid premium upgrades

Optimization History:

* reduced planning cost by 18%
* simplified hotel comparison strategy

Governance Status:
Normal

---

# 9. Add Runtime Integration

Integrate contextual cognition with:

* HITL guidance system
* semantic governance layer
* steering layer
* optimization engine
* experience layer
* workflow synthesis
* governance engine

Context should affect:

* interpretation
* clarification
* optimization recommendations
* governance strictness
* steering behavior
* execution adaptation

---

# 10. Add Context-Aware Clarification

VERY IMPORTANT.

Clarification should now become contextual.

Example:

Generic:
"What would you like to optimize?"

Contextual:
"You previously prioritized metro proximity.
Would you now like to trade convenience for lower cost?"

This is a HUGE UX improvement.

---

# 11. Add Drift + Instability Detection

The system should detect:

* optimization oscillation
* repeated priority reversal
* unstable steering
* escalating governance conflict

Examples:

* repeatedly changing from speed → quality → speed
* constantly reversing optimization choices

The system should:

* warn
* stabilize
* recommend operational consistency

WITHOUT:

* blocking collaboration unnecessarily

---

# 12. Add NEW Example File

Create:

examples/contextual_operational_cognition_demo.py

Demonstrate:

### Scenario BW — Contextual Guidance Interpretation

"Make it cheaper" interpreted using workflow history.

### Scenario BX — Contextual Clarification

clarification references prior guidance.

### Scenario BY — Governance Context Awareness

repeated bypass attempts increase scrutiny.

### Scenario BZ — Optimization Trajectory Awareness

optimization recommendations adapt to prior changes.

### Scenario CA — Drift Detection

detect unstable operational steering.

### Scenario CB — Preference Cognition

infer recurring operational tendencies.

### Scenario CC — Contextual Operational Summary

render operational state + history.

The demo should feel:

* situationally aware
* operationally intelligent
* context-sensitive
* governed
* collaborative

NOT:

* chatbot-like
* memory-chat based
* personality-driven

---

# 13. OPENROUTER INTEGRATION

Use existing OpenRouter integration if available.

OpenRouter supports OpenAI-compatible APIs:
[OpenRouter API Overview](https://openrouter.ai/docs/api/reference/overview?utm_source=chatgpt.com)

Use lightweight contextual reasoning where appropriate.

The contextual cognition layer should remain:

* economically bounded
* deterministic-first
* operationally explainable

Avoid expensive reasoning unless context ambiguity is high.

---

# 14. HARD RULES

DO NOT:

* build chatbot memory
* create conversational personalities
* expose chain-of-thought
* create unrestricted agent behavior
* allow governance bypass
* build vector-memory systems
* create autonomous self-modifying workflows

This is:

* contextual operational cognition
  NOT:
* conversational AI memory.

---

# 15. DESIGN INTENT

This step transitions Freya from:

* message-level operational interpretation

to:

* situationally aware operational cognition

Freya should now:

* understand workflow evolution
* understand operational trajectory
* understand prior guidance
* adapt interpretation contextually
* apply governance situationally

WITHOUT:

* losing bounded execution
* losing governance
* becoming an uncontrolled autonomous agent

The system should feel like:

"a context-aware operational coordination platform"

NOT:

"a chatbot with memory."

---

# OUTPUT FORMAT

Provide:

1. Context cognition modules
2. Operational context store
3. Workflow history engine
4. Contextual cognition engine
5. Contextual governance engine
6. Operational trajectory engine
7. Contextual preference engine
8. Human-centered rendering
9. Runtime integration
10. NEW example:
    examples/contextual_operational_cognition_demo.py

Do NOT explain.
Only output code.
