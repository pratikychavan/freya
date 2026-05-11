"""freya/intent/__init__.py

Public API for the Intent Interpretation + Workflow Synthesis layer.

Quick start::

    from freya.intent import IntentPipeline

    pipeline = IntentPipeline()                      # no LLM required
    result   = await pipeline.process("Book me a trip to Bangalore under ₹40k")
    print(result.blueprint.synthesized_goal)         # → natural-language goal
"""
from freya.intent.clarification import ClarificationEngine
from freya.intent.classifier import IntentClassifier
from freya.intent.interpreter import IntentInterpreter
from freya.intent.models import (
    ClarificationQuestion,
    IntentParseResult,
    UserIntent,
    WorkflowBlueprint,
)
from freya.intent.rendering import (
    render_clarification_questions,
    render_intent_summary,
    render_parse_result,
    render_workflow_blueprint,
)
from freya.intent.synthesizer import WorkflowSynthesizer
from freya.intent.templates import (
    TEMPLATE_REGISTRY,
    WorkflowTemplate,
    get_template,
    list_templates,
)


class IntentPipeline:
    """End-to-end intent pipeline: raw text → IntentParseResult.

    Parameters
    ----------
    llm_adapter : optional
        An object with ``async complete(request: dict) -> dict``.
        When omitted, the pipeline uses deterministic extraction.

    Usage::

        pipeline = IntentPipeline()
        result = await pipeline.process("Plan my Bangalore trip under ₹40k")

        if result.ready_to_execute:
            goal = result.blueprint.synthesized_goal
            # pass to runner...
        else:
            # present result.clarifications to the user
    """

    def __init__(self, llm_adapter: object | None = None) -> None:
        self._interpreter = IntentInterpreter(llm_adapter)
        self._synthesizer = WorkflowSynthesizer()
        self._clarification = ClarificationEngine()

    async def process(self, raw_input: str) -> IntentParseResult:
        """Parse *raw_input* and return a fully populated IntentParseResult."""
        intent = await self._interpreter.interpret(raw_input)

        clarifications = self._clarification.generate(intent)
        if clarifications:
            return IntentParseResult(
                intent=intent,
                blueprint=None,
                clarifications=clarifications,
                ready_to_execute=False,
                parse_method="llm" if self._interpreter._adapter else "deterministic",
            )

        blueprint = self._synthesizer.synthesize(intent)
        return IntentParseResult(
            intent=intent,
            blueprint=blueprint,
            clarifications=[],
            ready_to_execute=True,
            parse_method="llm" if self._interpreter._adapter else "deterministic",
        )


__all__ = [
    # Pipeline
    "IntentPipeline",
    # Components
    "IntentClassifier",
    "IntentInterpreter",
    "WorkflowSynthesizer",
    "ClarificationEngine",
    # Models
    "UserIntent",
    "WorkflowBlueprint",
    "ClarificationQuestion",
    "IntentParseResult",
    # Templates
    "WorkflowTemplate",
    "TEMPLATE_REGISTRY",
    "get_template",
    "list_templates",
    # Rendering
    "render_intent_summary",
    "render_workflow_blueprint",
    "render_clarification_questions",
    "render_parse_result",
]
