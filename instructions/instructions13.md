You are improving an existing Python SDK for an agent execution system.

The system already has:

* ExecutionEngine
* DAGRunner
* Tool system (Pydantic validated)
* Tracing system
* Policy system
* Memory layer
* Worker runtime
* Prompt model:
  class Prompt(BaseModel):
  template: str
  variables: Dict[str, Any] = {}
  system: Optional[str] = None
  metadata: Dict[str, Any] = {}
  def render(self) -> str: ...

Your task is to implement a **Prompt Registry**.

---

## Goal

Provide a clean way to:

* Register reusable prompts
* Retrieve prompts by name
* Inject variables at runtime
* Keep prompts traceable and consistent

---

## Requirements

### 1. Prompt Registry Class

Create:

class PromptRegistry

Responsibilities:

* store prompt templates
* return Prompt instances with variables injected

---

### 2. Registration

Method:

register(name: str, prompt: Prompt)

Behavior:

* store prompt by name
* raise error if name already exists

---

### 3. Retrieval

Method:

get(name: str, variables: dict | None = None) -> Prompt

Behavior:

* return a NEW Prompt instance
* merge provided variables with default variables
* do NOT mutate original prompt

---

### 4. Listing

Method:

list_prompts() -> list[str]

---

### 5. Error Handling

* If prompt not found → raise clear error
* If duplicate registration → raise error

---

### 6. ExecutionEngine Integration

Update LLM execution:

Allow task input to be:

{
"prompt_name": "summarize_v1",
"variables": {...}
}

Behavior:

* fetch prompt from registry
* inject variables
* render prompt
* send to LLM adapter

---

### 7. Trace Integration

When using registry:

* log:

  * prompt_name
  * template
  * variables
  * rendered_prompt

---

### 8. Example Prompts

Provide at least 2:

1. summarize_v1
   template: "Summarize the following:\n{text}"

2. explain_number
   template: "Explain what the number {value} represents in simple terms."

---

### 9. Example Usage

* register prompts
* create task using prompt_name
* run through ExecutionEngine
* print rendered prompt and result

---

## Constraints

* No persistence (in-memory only)
* No versioning system
* No external dependencies
* Keep implementation minimal and clean

---

## Output Format

Provide:

1. New file:
   freya/prompts/registry.py

2. Updated ExecutionEngine integration

3. Example usage

---

## Quality Bar

* No mutation bugs
* Clean separation of concerns
* Minimal API surface
* Easy to extend later

---

Do NOT explain. Just output code.
