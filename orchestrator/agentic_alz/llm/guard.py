"""Prompt-injection and tool-abuse guards for LLM stages.

The guards in this module are deliberately conservative and *deterministic*:
they run before any LLM context is built and after any LLM response is
received. They never call the LLM themselves.

Threat model (see ``docs/threat-model.md``):

* User input may contain hostile instructions ("ignore previous instructions",
  base64 payloads, fenced code blocks impersonating tool output).
* LLM responses may contain extra fields, missing fields, hallucinated
  citations, or exceed the per-stage token budget.

The guards do not try to detect "intent". They enforce shape: typed JSON in,
typed JSON out, no free-form text-as-instruction crossing the boundary.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from ..schema import SchemaValidationError, validate

# Patterns that suggest a prompt-injection attempt embedded in a string field.
# Matching does not block; it raises a structured error so callers can surface
# it in the audit log. Schema-level length and pattern constraints remain the
# primary defence; this is belt-and-braces.
_INJECTION_PATTERNS = (
    re.compile(r"(?i)ignore (all )?previous instructions"),
    re.compile(r"(?i)you are now"),
    re.compile(r"(?i)\bsystem prompt\b"),
    re.compile(r"(?i)<\|im_start\|>"),
    re.compile(r"(?i)```\s*(system|assistant)\s*\n"),
)

# Keys that must never be set by the LLM — they are computed server-side.
_FORBIDDEN_OUTPUT_KEYS = frozenset({"inputs_sha", "plan_sha", "schema_version"})

# Maximum length for any single string field flowing into a prompt context.
_MAX_INPUT_STRING_LEN = 4096


@dataclass(frozen=True)
class GuardFinding:
    """A single suspicious construct found in user input."""

    path: str
    pattern: str


class PromptInjectionDetected(ValueError):
    """Raised when guard detects an injection-shaped construct in user input."""

    def __init__(self, findings: list[GuardFinding]) -> None:
        self.findings = findings
        joined = ", ".join(f"{f.path}~{f.pattern}" for f in findings)
        super().__init__(f"prompt-injection-shaped content detected: {joined}")


class LLMOutputInvalid(ValueError):
    """Raised when an LLM response fails schema validation or sets a forbidden key."""


def sanitize_inputs(name: str, value: Any) -> None:
    """Validate ``value`` against the named schema and scan strings for injection.

    Args:
        name: Schema base name (e.g. ``"inputs"``).
        value: Decoded user input.

    Raises:
        SchemaValidationError: schema violation.
        PromptInjectionDetected: any string field matches an injection pattern
            or exceeds :data:`_MAX_INPUT_STRING_LEN`.
    """
    validate(name, value)
    findings: list[GuardFinding] = []
    _walk_strings(value, "", findings)
    if findings:
        raise PromptInjectionDetected(findings)


def validate_llm_output(
    name: str,
    value: Any,
    *,
    server_filled: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate an LLM-produced JSON object against the named schema.

    Server-controlled fields (``schema_version``, ``inputs_sha``, ``plan_sha``)
    are stripped from the LLM output and replaced with the values supplied in
    ``server_filled``. This prevents the LLM from forging content hashes.

    Returns:
        The merged, validated object.
    """
    if not isinstance(value, dict):
        raise LLMOutputInvalid(f"expected JSON object for {name}, got {type(value).__name__}")
    cleaned = {k: v for k, v in value.items() if k not in _FORBIDDEN_OUTPUT_KEYS}
    if server_filled:
        for k, v in server_filled.items():
            if k not in _FORBIDDEN_OUTPUT_KEYS and k != "schema_version":
                # Only the three named keys are server-controlled.
                continue
            cleaned[k] = v
    try:
        validate(name, cleaned)
    except SchemaValidationError as exc:
        raise LLMOutputInvalid(str(exc)) from exc
    return cleaned


def _walk_strings(node: Any, path: str, out: list[GuardFinding]) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            _walk_strings(v, f"{path}/{k}" if path else k, out)
        return
    if isinstance(node, list):
        for i, v in enumerate(node):
            _walk_strings(v, f"{path}[{i}]", out)
        return
    if isinstance(node, str):
        if len(node) > _MAX_INPUT_STRING_LEN:
            out.append(GuardFinding(path=path or "<root>", pattern="length-exceeded"))
            return
        for pat in _INJECTION_PATTERNS:
            if pat.search(node):
                out.append(GuardFinding(path=path or "<root>", pattern=pat.pattern))
                return
