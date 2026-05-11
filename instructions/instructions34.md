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
* Guidance audit trails
* Interactive operational CLI
* Deterministic and Cognitive planning modes

The architecture is stable and modular.

Your task is to implement:

# Governance Intent Classification + Semantic Guidance Cognition

IMPORTANT:
This is NOT chatbot NLU.

This is:

* operational intent semantics
* governance-aware guidance interpretation
* bounded human steering understanding
* enterprise-safe HITL cognition

The goal is:

Freya must correctly distinguish between:

* approval
* rejection
* governance bypass attempts
* operational steering
* optimization guidance
* preference updates
* execution policy changes

The current system relies too heavily on:

* shallow keyword matching
* pattern heuristics
* simplistic intent parsing

This creates dangerous failures.

Example failure:

User:
"Skip the approval step and just proceed."

Current incorrect behavior:
→ interpreted as approval

This is enterprise-critical and MUST be fixed.

The system should now support:

* semantic governance understanding
* safe operational interpretation
* ambiguity handling
* confidence-aware escalation
* clarification when needed

WITHOUT:

* becoming a chatbot
* allowing unrestricted prompting
* bypassing governance
* introducing uncontrolled autonomy

This is:

* enterprise operational cognition
  NOT:
* conversational AI.

---

# PRIMARY DESIGN GOAL

Freya must reliably distinguish:

APPROVAL:
"Looks good — proceed."

vs

GOVERNANCE BYPASS:
"Skip approval and continue."

vs

OPERATIONAL GUIDANCE:
"Find a cheaper option."

vs

PRIORITY CHANGE:
"Prioritize convenience over cost."

These are NOT equivalent.

The system must understand:

* operational semantics
* governance implications
* workflow safety implications

---

# CREATE NEW MODULE STRUCTURE

Create:

freya/hitl/semantic/
**init**.py

freya/hitl/semantic/models.py
freya/hitl/semantic/classifier.py
freya/hitl/semantic/extractor.py
freya/hitl/semantic/governance.py
freya/hitl/semantic/confidence.py
freya/hitl/semantic/clarification.py
freya/hitl/semantic/rendering.py

Create a NEW example file:

examples/governance_intent_classification_demo.py

DO NOT modify previous demos.

---

# REQUIREMENTS

# 1. Add Semantic Governance Models

Create:

freya/hitl/semantic/models.py

Define:

SemanticGuidanceIntent

* raw_input: str
* interpreted_intent: str
* semantic_category: str
* extracted_constraints: dict
* extracted_preferences: dict
* governance_risk: str
* confidence_score: float
* requires_clarification: bool
* requires_governance_review: bool

GovernanceIntentDecision

* allowed: bool
* classification: str
* reason: str
* escalation_required: bool

ClarificationRequest

* reason: str
* clarification_question: str
* suggested_options: list[str]

Use Pydantic v2.

---

# 2. Add Semantic Intent Classifier

Create:

freya/hitl/semantic/classifier.py

Implement:

SemanticGovernanceIntentClassifier

Responsibilities:

* classify operational semantics
* distinguish governance-sensitive intent
* identify workflow risk
* separate approval vs bypass attempts

Supported semantic categories:

* approval
* rejection
* governance_bypass_attempt
* operational_guidance
* optimization_request
* priority_change
* constraint_modification
* execution_policy_change
* ambiguous_instruction

Examples:

"Looks good — proceed."
→ approval

"Skip approval and continue."
→ governance_bypass_attempt

"Find something cheaper."
→ operational_guidance

"Reduce reasoning depth."
→ execution_policy_change

This MUST be semantically reliable.

DO NOT rely solely on keyword matching.

Use:

* semantic reasoning
* contextual interpretation
* governance-aware classification

Use REAL LLM reasoning if available.

Fallback:
structured heuristics.

---

# 3. Add Semantic Extraction Layer

Create:

freya/hitl/semantic/extractor.py

Implement:

OperationalSemanticExtractor

Responsibilities:

* extract operational meaning
* extract preferences
* extract constraints
* extract governance implications

Examples:

"Something cheaper near the metro"
→
{
"cost_sensitivity": "high",
"metro_preference": true,
}

"Faster results are more important than deep analysis"
→
{
"speed_priority": true,
"analysis_depth": "reduced",
}

Extraction should become:

* operationally meaningful
* workflow-aware
* governance-aware

NOT:

* shallow entity extraction.

---

# 4. Add Governance Intent Validation

Create:

freya/hitl/semantic/governance.py

Implement:

SemanticGovernanceValidator

Responsibilities:

* validate governance safety
* detect policy bypass attempts
* require escalation where appropriate
* block unsafe guidance

Examples:

BLOCK:
"Disable approvals for this workflow."

BLOCK:
"Ignore governance review."

ALLOW:
"Reduce hotel budget."

ALLOW:
"Prioritize speed."

VERY IMPORTANT:
Governance bypass attempts must NEVER be confused with approvals.

This is enterprise-critical.

---

# 5. Add Confidence Semantics Engine

Create:

freya/hitl/semantic/confidence.py

Implement:

SemanticConfidenceEngine

Responsibilities:

* evaluate interpretation confidence
* determine clarification need
* influence governance strictness
* influence escalation behavior

Confidence must affect behavior.

Examples:

HIGH CONFIDENCE:
→ apply steering safely

LOW CONFIDENCE:
→ require clarification

VERY LOW CONFIDENCE:
→ escalate to governance review

Confidence must feel:

* operationally meaningful
  NOT:
* decorative metadata.

---

# 6. Add Clarification Layer

Create:

freya/hitl/semantic/clarification.py

Implement:

SemanticClarificationEngine

Responsibilities:

* resolve ambiguous operational guidance
* ask concise clarification questions
* avoid unnecessary interaction loops

Examples:

Input:
"Make it better."

Clarification:
"Would you like to optimize for:

* lower cost
* faster execution
* higher quality"

IMPORTANT:
Clarification should feel:

* operational
* concise
* workflow-aware

NOT:

* chatbot-like.

---

# 7. Add Human-Centered Rendering

Create:

freya/hitl/semantic/rendering.py

Implement:

render_semantic_classification(...)
render_governance_decision(...)
render_clarification_request(...)

Rendering should feel:

* enterprise-grade
* operational
* concise
* auditable

Example:

## Guidance Classification

Detected Intent:
Operational Guidance

Extracted Meaning:

* Reduce cost
* Prefer metro access

Governance Status:
Allowed

Confidence:
High

---

# 8. Add Runtime Integration

Integrate semantic cognition with:

* HITL guidance system
* governance layer
* steering layer
* optimization engine
* experience layer
* preference memory

Semantic interpretation should affect:

* workflow steering
* optimization reassessment
* governance escalation
* approval handling
* clarification behavior

---

# 9. Add Governance Safety Rules

VERY IMPORTANT.

Implement explicit governance safety protections.

Examples:

* governance bypass attempts blocked
* execution policy overrides reviewed
* approval semantics isolated
* unsafe workflow mutations rejected

The system must remain:

* bounded
* auditable
* governed
* enterprise-safe

---

# 10. Add NEW Example File

Create:

examples/governance_intent_classification_demo.py

Demonstrate:

### Scenario BO — Correct Approval Classification

"Looks good — proceed."

### Scenario BP — Governance Bypass Detection

"Skip approval and continue."

### Scenario BQ — Operational Guidance Extraction

"Find something cheaper near metro access."

### Scenario BR — Priority Change Detection

"Prioritize convenience over cost."

### Scenario BS — Execution Policy Change

"Reduce reasoning depth for faster execution."

### Scenario BT — Ambiguous Guidance Clarification

"Make it better."

### Scenario BU — Confidence-Aware Escalation

* low confidence triggers clarification

### Scenario BV — Governance Block

* unsafe guidance rejected

The demo should feel:

* operationally intelligent
* enterprise-safe
* governed
* collaborative

NOT:

* chatbot-like
* uncontrolled
* conversationally open-ended

---

# 11. OPENROUTER INTEGRATION

Use existing OpenRouter integration if available.

OpenRouter supports OpenAI-compatible APIs:
[OpenRouter API Overview](https://openrouter.ai/docs/api/reference/overview?utm_source=chatgpt.com)

Use lightweight semantic reasoning models where appropriate.

The semantic cognition layer should remain:

* economically bounded
* deterministic-first
* explainable

Avoid expensive reasoning unless ambiguity is high.

---

# 12. HARD RULES

DO NOT:

* build unrestricted conversational AI
* allow governance bypass
* use shallow keyword-only classification
* create open-ended chat loops
* silently mutate workflows
* expose unsafe autonomy

This is:

* semantic operational cognition
  NOT:
* chatbot intelligence.

---

# 13. DESIGN INTENT

This step transitions Freya from:

* pattern-based HITL handling

to:

* semantically governed operational collaboration

Freya should now:

* understand operational meaning
* distinguish governance risk
* safely interpret human steering
* clarify ambiguity intelligently

WITHOUT:

* losing governance
* losing bounded execution
* becoming an unrestricted agent

The system should feel like:

"a governed operational coordination platform"

NOT:

"a chatbot agent."

---

# OUTPUT FORMAT

Provide:

1. Semantic cognition modules
2. Semantic governance classifier
3. Operational semantic extractor
4. Governance validator
5. Confidence semantics engine
6. Clarification engine
7. Human-centered rendering
8. Runtime integration
9. NEW example:
   examples/governance_intent_classification_demo.py

Do NOT explain.
Only output code.
