You are working inside the Freya SDK repository.

Freya already supports:

* ExecutionEngine
* DAGRunner
* IterativePlannerRunner
* PlanningContext
* Observation-aware planning
* Validation + Repair loop
* Runtime failure recovery
* ToolRegistry
* PromptRegistry
* PromptCapabilityRegistry
* PlanningMode
* Memory layer
* Trace system
* Capability-aware planning
* Deterministic and Cognitive planner modes

The architecture is stable and modular.

Your task is to implement:

# Governance Abstraction Layer (STEP 1 of HITL)

IMPORTANT:
This step does NOT implement workflow pausing or resume.

This step ONLY introduces:

* governance evaluation
* intervention policies
* approval decision abstractions
* governance trace events

DO NOT add:

* UI
* persistence
* approval APIs
* workflow pausing
* resume logic

This is ONLY the governance decision infrastructure.

---

# ARCHITECTURE GOAL

Freya planners currently:

* generate DAG fragments

Freya runtime currently:

* validates and executes DAG fragments

We now need a governance layer that decides:

"Should this proposed DAG fragment require human approval before execution?"

Governance must remain:

* separate from planner
* separate from runtime execution
* deterministic
* observable

---

# REQUIREMENTS

## 1. Add InterventionDecision Enum

Create:

freya/governance/models.py

Define:

class InterventionDecision(str, Enum):
APPROVE = "approve"
REQUIRE_APPROVAL = "require_approval"
REJECT = "reject"

---

## 2. Add GovernanceDecision model

Define:

GovernanceDecision:

* decision: InterventionDecision
* reason: str
* risk_level: str | None = None
* triggered_policies: list[str] = []

Use Pydantic v2.

---

## 3. Add InterventionPolicy Base Class

Create:

freya/governance/base.py

Define:

class InterventionPolicy(ABC):

```
def evaluate(
    self,
    planning_context,
    proposed_dag,
) -> GovernanceDecision:
    ...
```

Policies MUST:

* remain deterministic
* NOT execute tools
* NOT mutate memory
* NOT call planner

---

## 4. Add GovernanceEngine

Create:

freya/governance/engine.py

Responsibilities:

* register policies
* evaluate policies
* aggregate governance decisions

Methods:

* register(policy)
* evaluate(planning_context, proposed_dag)

Aggregation rules:

1. Any REJECT => final REJECT
2. Any REQUIRE_APPROVAL => final REQUIRE_APPROVAL
3. Otherwise => APPROVE

Return GovernanceDecision.

---

## 5. Add Example Policies

Create:

freya/governance/policies.py

Implement:

### CognitiveModeApprovalPolicy

Behavior:

* if planning_mode == COGNITIVE
  → REQUIRE_APPROVAL

Reason:
"Cognitive mode workflows require approval."

---

### DangerousToolPolicy

Behavior:

* if DAG contains dangerous tool names:

  * delete_data
  * send_money
  * external_mutation

→ REQUIRE_APPROVAL

---

### ExcessiveRecoveryPolicy

Behavior:

* if recovery attempts > threshold
  → REQUIRE_APPROVAL

---

## 6. Integrate Governance Evaluation

Update IterativePlannerRunner.

After:

* planner generates DAG
* validation succeeds

BUT BEFORE execution:

Call GovernanceEngine.evaluate()

Store GovernanceDecision.

For now:

* execution should CONTINUE normally
* DO NOT pause execution yet

This step is ONLY governance evaluation infrastructure.

---

## 7. Governance Trace Events

Add trace events:

governance_evaluated
governance_policy_triggered

Example payloads:

{
"decision": "require_approval",
"reason": "Cognitive mode workflows require approval."
}

{
"policy": "DangerousToolPolicy"
}

---

## 8. Governance Observations

Add governance observations to planner context.

Example summary:

"governance flagged DAG for approval due to cognitive mode"

DO NOT expose raw policy internals.

---

## 9. Example

Update examples/run_planner.py

Demonstrate:

### Deterministic workflow

* governance decision = APPROVE

### Cognitive workflow

* governance decision = REQUIRE_APPROVAL

### Dangerous tool workflow

* governance decision = REQUIRE_APPROVAL

Print:

* triggered policies
* governance decisions
* governance reasons

Execution should still continue for now.

NO pausing yet.

---

## 10. HARD RULES

DO NOT:

* pause workflows
* implement resume APIs
* add databases
* add user interfaces
* allow governance layer to mutate execution
* allow planner to bypass governance

Governance must remain:

* advisory
* deterministic
* observable
* separate from runtime

---

## 11. DESIGN INTENT

This step introduces:

Governed Adaptive Execution

Planner:

* proposes

Governance:

* evaluates risk

Runtime:

* executes

Human approval mechanisms come later.

This step ONLY establishes governance architecture.

---

# OUTPUT FORMAT

Provide:

1. Governance models
2. Governance engine
3. Example policies
4. Runner integration
5. Trace integration
6. Updated examples

Do NOT explain.
Only output code.
