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
* Clarification handling
* Operational steering
* Constraint negotiation
* Recommendation rendering
* Preference memory
* Deterministic and Cognitive planning modes

The architecture is stable and modular.

Your task is to implement:

# Proactive Operational Optimization Layer

IMPORTANT:
This is NOT autonomous AI behavior.

This is:

* governed operational optimization
* bounded recommendation generation
* continuous workflow improvement detection
* proactive tradeoff suggestion

The goal is:

Freya should no longer ONLY react to user steering.

Freya should:

* proactively identify better operational paths
* recommend safer/faster/cheaper optimizations
* continuously evaluate workflow efficiency
* surface optimization opportunities

WITHOUT:

* autonomously mutating workflows
* bypassing governance
* silently changing execution behavior
* becoming an uncontrolled agent

This is:

* operational optimization
  NOT:
* autonomous workflow mutation.

---

# PRIMARY DESIGN GOAL

Current behavior:

User:
"Reduce cost."

Freya:
"Okay, reprioritizing."

NEW behavior:

Freya:
"I found an alternative hotel that reduces total trip cost by ₹6,200
while increasing commute time by only ~15 minutes/day.

Would you like to apply this optimization?"

This should feel:

* operationally intelligent
* proactive
* collaborative
* governed

NOT:

* autonomous
* agentic
* chaotic

---

# CREATE NEW MODULE STRUCTURE

Create:

freya/optimization/
**init**.py

freya/optimization/models.py
freya/optimization/engine.py
freya/optimization/scoring.py
freya/optimization/policies.py
freya/optimization/rendering.py
freya/optimization/recommendations.py

Create a NEW example file:

examples/proactive_optimization_demo.py

DO NOT modify previous demos.

---

# REQUIREMENTS

# 1. Add Optimization Models

Create:

freya/optimization/models.py

Define:

OptimizationOpportunity

* opportunity_id: str
* title: str
* description: str
* optimization_type: str
* estimated_cost_delta: float | None
* estimated_time_delta: float | None
* estimated_quality_delta: float | None
* confidence_score: float
* governance_impact: str | None

OptimizationProposal

* proposal_id: str
* reason: str
* opportunities: list[OptimizationOpportunity]
* recommended_action: str
* requires_approval: bool

OptimizationEvaluation

* total_savings: float
* execution_impact: str
* governance_risk: str
* confidence_score: float

Use Pydantic v2.

---

# 2. Add Proactive Optimization Engine

Create:

freya/optimization/engine.py

Implement:

ProactiveOptimizationEngine

Responsibilities:

* continuously inspect workflow state
* identify operational inefficiencies
* detect optimization opportunities
* generate proactive proposals

Examples:

* cheaper equivalent hotel
* lower-cost planning strategy
* reduced cognitive reasoning path
* lower delegation depth
* reduced approval overhead
* lower recovery retry depth

IMPORTANT:
The engine should:

* recommend optimizations
  NOT:
* automatically apply them

This distinction is CRITICAL.

---

# 3. Add Optimization Scoring Engine

Create:

freya/optimization/scoring.py

Implement:

OptimizationScoringEngine

Responsibilities:

* evaluate optimization tradeoffs
* estimate operational value
* compare benefit vs impact
* estimate confidence

Scoring factors:

* economics impact
* workflow quality impact
* governance risk
* execution latency
* cognitive spend reduction
* delegation reduction

Example:
Savings:
₹5,200

Impact:
+15 minutes commute/day

Confidence:
0.87

---

# 4. Add Optimization Governance Policies

Create:

freya/optimization/policies.py

Implement:

OptimizationGovernancePolicy

Responsibilities:

* prevent unsafe optimization suggestions
* require approval for risky optimizations
* prevent governance bypassing
* bound optimization aggressiveness

Examples:

* reducing governance checks requires approval
* skipping deep reasoning may require review
* lowering workflow quality too aggressively blocked

Optimization must remain:

* governed
* explainable
* bounded

---

# 5. Add Recommendation Engine

Create:

freya/optimization/recommendations.py

Implement:

OperationalOptimizationRecommender

Responsibilities:

* generate human-centered optimization suggestions
* summarize tradeoffs
* explain benefits clearly
* recommend best operational path

Examples:

"I found a hotel package that saves ₹5,200
while keeping commute time nearly identical."

"Current planning strategy is consuming more budget than expected.
Switch to faster planning mode?"

"Deep hotel comparison is unlikely to improve results significantly.
Skip advanced analysis?"

This layer is VERY important.

It creates:

* perceived operational intelligence
  WITHOUT:
* uncontrolled autonomy.

---

# 6. Add Human-Centered Rendering

Create:

freya/optimization/rendering.py

Implement:

render_optimization_proposal(...)
render_optimization_summary(...)
render_optimization_evaluation(...)

Rendering must feel:

* concise
* operational
* executive-friendly

NOT:

* verbose AI chat.

Example:

## Optimization Opportunity

A lower-cost hotel option is available.

Savings:
₹6,200

Tradeoff:
~15 minutes additional commute/day

Confidence:
87%

Recommendation:
Apply optimization

Requires Approval:
No

---

# 7. Add Runtime Integration

Integrate optimization engine with:

* steering layer
* economics layer
* governance layer
* adaptive execution layer
* experience layer

Optimization opportunities should react to:

* workflow economics
* cognitive cost
* delegation depth
* governance overhead
* runtime failures
* execution latency

---

# 8. Add Continuous Optimization Evaluation

VERY IMPORTANT.

Optimization should become:

* continuous
* workflow-aware
* context-aware

The engine should periodically:

* reassess workflow efficiency
* reassess economics
* reassess quality/cost balance

WITHOUT:

* constantly interrupting users
* creating optimization spam

Bound optimization frequency carefully.

---

# 9. Add Optimization Confidence Semantics

Optimization confidence must affect:

* recommendation strength
* approval requirements
* rendering language
* aggressiveness

Examples:

High confidence:
"Strongly recommended"

Low confidence:
"Possible optimization available"

Confidence should feel:

* operationally meaningful
  NOT:
* decorative metadata.

---

# 10. Add NEW Example File

Create:

examples/proactive_optimization_demo.py

Demonstrate:

### Scenario BB — Cost Optimization

* proactive lower-cost recommendation

### Scenario BC — Cognitive Spend Optimization

* reduce unnecessary reasoning depth

### Scenario BD — Delegation Optimization

* reduce excessive child workflows

### Scenario BE — Governance-Aware Optimization

* optimization requiring approval

### Scenario BF — Continuous Optimization Reassessment

* workflow reevaluated during execution

### Scenario BG — Confidence-Aware Recommendations

* strong vs weak optimization confidence

### Scenario BH — Economics + Optimization Integration

* optimization changes workflow economics

The demo should feel:

* proactive
* intelligent
* operational
* collaborative

NOT:

* autonomous
* chaotic
* chatbot-like

---

# 11. OPENROUTER INTEGRATION

Use existing OpenRouter integration if available.

OpenRouter is OpenAI-compatible:
[OpenRouter API Overview](https://openrouter.ai/docs/api/reference/overview?utm_source=chatgpt.com)

OpenRouter supports OpenAI SDK compatibility:
[OpenRouter OpenAI SDK Guide](https://openrouter.ai/docs/guides/community/openai-sdk?utm_source=chatgpt.com)

Use model routing where appropriate:

* lightweight optimization analysis
* stronger tradeoff reasoning
* cheaper summarization

Optimization reasoning should remain:

* economically bounded
* explainable
* governed

---

# 12. HARD RULES

DO NOT:

* auto-apply risky optimizations
* create self-modifying workflows
* create recursive optimization loops
* bypass governance
* create uncontrolled autonomy
* build chatbot loops
* expose runtime internals to user views

This is:

* bounded governed optimization
  NOT:
* autonomous agent behavior.

---

# 13. DESIGN INTENT

This step transitions Freya from:

* reactive operational coordination

to:

* proactive operational optimization

Freya should now feel:

* operationally intelligent
* proactively helpful
* economically aware
* continuously optimizing

WITHOUT:

* losing governance
* losing bounded behavior
* becoming an autonomous agent

The system should feel like:

"an intelligent operational advisor"

NOT:

"a self-running AI system."

---

# OUTPUT FORMAT

Provide:

1. Optimization layer modules
2. Proactive optimization engine
3. Optimization scoring engine
4. Governance policies
5. Recommendation engine
6. Human-centered rendering
7. Runtime integration
8. NEW example:
   examples/proactive_optimization_demo.py

Do NOT explain.
Only output code.
