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
* Human-readable workflow progress
* Narrative summaries
* Progressive disclosure rendering
* Deterministic and Cognitive planning modes

The architecture is stable and modular.

Your task is to implement:

# Intent Interpretation + Workflow Synthesis Layer

IMPORTANT:
This is NOT chatbot development.

This is:

* goal-oriented operational interaction
* intent interpretation
* workflow synthesis
* constraint extraction
* clarification handling

The goal is:

Users should express:

* goals
* preferences
* constraints

WITHOUT:

* understanding workflows
* understanding orchestration
* configuring DAGs
* understanding runtime semantics

Freya should synthesize governed adaptive workflows automatically.

---

# PRIMARY DESIGN GOAL

The user should say:

"Plan my Bangalore trip under ₹40k."

NOT:

"Create a workflow with subworkflows."

This is:

* intent-first interaction
  NOT:
* workflow-first interaction.

---

# CREATE NEW MODULE STRUCTURE

Create:

freya/intent/
**init**.py

freya/intent/models.py
freya/intent/interpreter.py
freya/intent/classifier.py
freya/intent/synthesizer.py
freya/intent/clarification.py
freya/intent/templates.py
freya/intent/rendering.py

Create a NEW example file:

examples/intent_layer_demo.py

DO NOT modify previous demos.

---

# REQUIREMENTS

# 1. Add Intent Models

Create:

freya/intent/models.py

Define:

UserIntent

* raw_input: str
* inferred_domain: str | None
* primary_goal: str
* constraints: dict
* preferences: dict
* extracted_entities: list[str]
* ambiguity_score: float
* requires_clarification: bool

WorkflowBlueprint

* workflow_type: str
* suggested_subworkflows: list[str]
* governance_requirements: list[str]
* estimated_complexity: str
* recommended_strategy: str

ClarificationQuestion

* question: str
* reason: str
* options: list[str] | None

Use Pydantic v2.

---

# 2. Add Intent Interpreter

Create:

freya/intent/interpreter.py

Implement:

IntentInterpreter

Responsibilities:

* parse natural language goals
* extract constraints
* identify preferences
* identify ambiguity
* build UserIntent

Example input:

"Plan my Bangalore trip under ₹40k with hotels near the client office."

Extract:

* goal = travel planning
* constraint = budget ₹40k
* preference = proximity
* entity = Bangalore

Use REAL LLM extraction if available.

Fallback:
deterministic parsing heuristics.

---

# 3. Add Intent Classification

Create:

freya/intent/classifier.py

Implement:

IntentClassifier

Responsibilities:

* infer workflow domain
* classify operational intent
* route toward workflow templates

Supported domains:

* business_travel
* incident_response
* data_pipeline
* scheduling
* procurement

Use:

* lightweight classification
* deterministic fallback

---

# 4. Add Workflow Synthesis Layer

Create:

freya/intent/synthesizer.py

Implement:

WorkflowSynthesizer

Responsibilities:

* convert UserIntent → WorkflowBlueprint
* infer subworkflows
* infer governance requirements
* infer execution strategy
* infer complexity

Example:

business_travel →

* FindFlights
* FindHotels
* BuildItinerary
* EstimateCosts

Governance:

* budget approvals

Strategy:

* deterministic-first

---

# 5. Add Clarification System

Create:

freya/intent/clarification.py

Implement:

ClarificationEngine

Responsibilities:

* detect ambiguous intents
* generate clarification questions
* minimize unnecessary clarification

Example:

Input:
"Book me a hotel in Bangalore."

Clarification:
"Do you prefer lower cost or proximity to the meeting venue?"

This is VERY important.

Clarification should feel:

* operational
  NOT:
* conversational fluff.

---

# 6. Add Workflow Templates

Create:

freya/intent/templates.py

Implement reusable workflow templates.

Example:

BUSINESS_TRAVEL_TEMPLATE
INCIDENT_RESPONSE_TEMPLATE
DATA_PIPELINE_TEMPLATE

Templates should define:

* workflow archetypes
* common subworkflows
* governance defaults
* execution strategies

DO NOT hardcode giant if/else chains.

---

# 7. Add Intent Rendering Layer

Create:

freya/intent/rendering.py

Implement:

render_intent_summary(...)
render_workflow_blueprint(...)
render_clarification(...)

Example output:

## Detected Intent

Goal:
Plan Bangalore business trip

Constraints:

* Budget: ₹40,000

Preferences:

* Hotel near client office

## Suggested Workflow

* Find Flights
* Find Hotels
* Build Itinerary
* Estimate Costs

Governance:

* Budget approval required for premium hotels

---

# 8. Add Experience Layer Integration

Integrate with:

* experience layer
* narrative summaries
* progress rendering

Intent summaries should become:

* human-readable
* product-oriented
* non-technical

---

# 9. Add Intent Confidence + Ambiguity

Intent system should expose:

* ambiguity_score
* requires_clarification

Example:

ambiguity_score=0.82
requires_clarification=True

Clarification should only happen when genuinely needed.

Avoid:

* annoying question loops.

---

# 10. Add NEW Example File

Create:

examples/intent_layer_demo.py

Demonstrate:

### Scenario AQ — Clear Intent

* business travel request
* successful workflow synthesis

### Scenario AR — Ambiguous Intent

* clarification question generated

### Scenario AS — Workflow Blueprint Rendering

* show synthesized workflow

### Scenario AT — Constraint Extraction

* budget + preferences extracted

### Scenario AU — Intent → Experience Integration

* synthesized workflow feeds experience layer

The example should feel:

* product-like
* human-centered
* operational
* non-technical

NOT:

* workflow-engine-centric

---

# 11. HARD RULES

DO NOT:

* build chatbot loops
* create fake personalities
* expose runtime semantics
* expose DAG internals
* expose orchestration mechanics
* create open-ended conversational agents

This is:

* operational intent interaction
  NOT:
* AI companionship.

---

# 12. DESIGN INTENT

This step transitions Freya from:

* workflow-centric interaction

to:

* intent-centric governed execution

Users express:

* goals
* constraints
* preferences

Freya synthesizes:

* workflows
* governance
* strategies
* orchestration

The system should feel like:

"an intelligent operations coordinator"

NOT:
"a workflow engine."

---

# OUTPUT FORMAT

Provide:

1. Intent layer modules
2. Intent interpreter
3. Intent classifier
4. Workflow synthesizer
5. Clarification engine
6. Workflow templates
7. Rendering helpers
8. NEW example:
   examples/intent_layer_demo.py

Do NOT explain.
Only output code.
