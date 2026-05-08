"""Rule-based runtime failure classifier.

Classifies exceptions or error strings into a structured dict without using
an LLM — ensuring deterministic, bounded behaviour in the recovery loop.
"""
from __future__ import annotations

# Lowercase markers that indicate a non-recoverable failure regardless of
# the exception type.
_UNRECOVERABLE_MARKERS = frozenset({
    "unrecoverable",
    "fatal",
    "policy_block",
    "policyblock",
    "not_recoverable",
})


def classify_failure(error: "Exception | str") -> dict:
    """Classify a runtime failure into a structured result.

    Parameters
    ----------
    error:
        Either an actual Exception (enables ``isinstance`` checks) or an error
        string (e.g. as stored in ``TaskResult.error``).

    Returns
    -------
    dict with keys:
        ``failure_category`` — one of TOOL_EXCEPTION, TIMEOUT, POLICY_BLOCK,
            INVALID_OUTPUT, LLM_FAILURE
        ``recoverable``      — bool
        ``summary``          — compact human-readable string (≤ 120 chars)
    """
    if isinstance(error, Exception):
        exc: Exception | None = error
        name = type(error).__name__.lower()
        msg = str(error).lower()
    else:
        exc = None
        name = ""
        msg = (error or "").lower()

    combined = f"{name} {msg}"

    # ------------------------------------------------------------------ #
    # Non-recoverable markers take highest priority.                       #
    # ------------------------------------------------------------------ #
    if any(m in combined for m in _UNRECOVERABLE_MARKERS):
        return {
            "failure_category": _detect_category(combined),
            "recoverable": False,
            "summary": f"non-recoverable failure: {str(error)[:120]}",
        }

    # ------------------------------------------------------------------ #
    # isinstance checks on actual exceptions (most precise).              #
    # ------------------------------------------------------------------ #
    if exc is not None:
        if isinstance(exc, TimeoutError):
            return {
                "failure_category": "TIMEOUT",
                "recoverable": True,
                "summary": f"timeout: {str(exc)[:120]}",
            }
        if isinstance(exc, KeyError):
            return {
                "failure_category": "TOOL_EXCEPTION",
                "recoverable": True,
                "summary": f"key error: {str(exc)[:120]}",
            }
        if isinstance(exc, ValueError):
            return {
                "failure_category": "INVALID_OUTPUT",
                "recoverable": True,
                "summary": f"value error: {str(exc)[:120]}",
            }

    # ------------------------------------------------------------------ #
    # String pattern matching for serialised error messages.              #
    # ------------------------------------------------------------------ #
    if "timeout" in combined or "timed out" in combined:
        return {
            "failure_category": "TIMEOUT",
            "recoverable": True,
            "summary": f"timeout: {str(error)[:120]}",
        }

    if "policy" in combined:
        return {
            "failure_category": "POLICY_BLOCK",
            "recoverable": False,
            "summary": f"policy block: {str(error)[:120]}",
        }

    if "invalid output" in combined or "invalid_output" in combined:
        return {
            "failure_category": "INVALID_OUTPUT",
            "recoverable": True,
            "summary": f"invalid output: {str(error)[:120]}",
        }

    if "llm" in combined or "llmadapter" in combined or "lm_adapter" in combined:
        return {
            "failure_category": "LLM_FAILURE",
            "recoverable": True,
            "summary": f"LLM failure: {str(error)[:120]}",
        }

    if "keyerror" in combined or "key error" in combined:
        return {
            "failure_category": "TOOL_EXCEPTION",
            "recoverable": True,
            "summary": f"key error: {str(error)[:120]}",
        }

    # Default: treat as a recoverable tool exception.
    return {
        "failure_category": "TOOL_EXCEPTION",
        "recoverable": True,
        "summary": f"tool exception: {str(error)[:120]}",
    }


def _detect_category(combined: str) -> str:
    """Pick the most specific failure category from a combined name+msg string."""
    if "timeout" in combined or "timed out" in combined:
        return "TIMEOUT"
    if "policy" in combined:
        return "POLICY_BLOCK"
    if "invalid output" in combined or "invalid_output" in combined:
        return "INVALID_OUTPUT"
    if "llm" in combined:
        return "LLM_FAILURE"
    return "TOOL_EXCEPTION"
