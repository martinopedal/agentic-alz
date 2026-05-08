"""Interview stage runtime.

Takes the conversation captured by the Interview prompt
(`prompts/interview.v1.md`) and produces a schema-valid ``inputs.yaml``
object. Two modes:

* **Offline** (default, used by CI/evals): the transcript already contains
  a final ``assistant`` turn whose ``content`` is the JSON object the model
  produced. The runtime just parses, sanitises and validates it. **No LLM
  call is made.** This is what the eval harness uses, and it is the only
  mode wired into v1 — the live provider client lands behind a separate
  human-merged PR.

* **Live**: invoke an allowlisted ``interview``-role model via
  :func:`agentic_alz.llm.models.assert_frontier`. The provider client
  itself is not wired in v1; calling :func:`run_interview_live` raises
  :class:`LiveModeNotImplemented`. The function exists so we can lock in
  the contract (single non-streaming call, no tool/function calling,
  budget-checked) and so tests can exercise the gating logic.

In both modes the LLM output is treated as untrusted: it goes through
:func:`agentic_alz.llm.guard.validate_llm_output` (which strips
server-controlled keys like ``schema_version``) and then through the
``inputs`` JSON Schema before being returned. User free text never
escapes a string-typed schema field.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..budget import Budget, TokenMeter
from ..llm.guard import LLMOutputInvalid, validate_llm_output
from ..llm.models import assert_frontier

# Shape of one transcript line. The transcript is JSONL with ``role`` in
# {"system", "user", "assistant"} and ``content`` as a string. The final
# entry MUST be ``assistant`` and its ``content`` MUST be a single JSON
# object; everything before it is conversational context that is NOT
# re-fed to any model in offline mode.
_VALID_ROLES = frozenset({"system", "user", "assistant"})


class TranscriptError(ValueError):
    """Raised when a transcript file is malformed."""


class LiveModeNotImplemented(NotImplementedError):
    """Raised by :func:`run_interview_live` until a provider client lands."""


@dataclass(frozen=True)
class TranscriptTurn:
    """One line of the JSONL transcript."""

    role: str
    content: str


def load_transcript(path: str | Path) -> list[TranscriptTurn]:
    """Load a JSONL transcript, validating shape but not content.

    Raises:
        FileNotFoundError: ``path`` does not exist.
        TranscriptError: any line is not a JSON object with valid
            ``role``/``content``, or the file is empty.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"transcript not found: {p}")
    turns: list[TranscriptTurn] = []
    for lineno, raw in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TranscriptError(f"line {lineno}: not valid JSON: {exc}") from exc
        if not isinstance(obj, dict):
            raise TranscriptError(f"line {lineno}: expected JSON object")
        role = obj.get("role")
        content = obj.get("content")
        if role not in _VALID_ROLES:
            raise TranscriptError(
                f"line {lineno}: role {role!r} not in {sorted(_VALID_ROLES)}"
            )
        if not isinstance(content, str):
            raise TranscriptError(f"line {lineno}: content must be a string")
        turns.append(TranscriptTurn(role=role, content=content))
    if not turns:
        raise TranscriptError("transcript is empty")
    return turns


def run_interview_offline(transcript: list[TranscriptTurn]) -> dict[str, Any]:
    """Run the Interview stage against a pre-recorded transcript.

    The terminal turn must be ``assistant`` and its ``content`` must be a
    single JSON object that validates against ``inputs.schema.json``. This
    is the contract the live runtime would also enforce.

    The function does **not** issue an LLM call and does **not** re-feed
    earlier turns anywhere — they are kept only so the eval harness can
    exhibit the conversational shape that produced the output.

    Returns:
        The validated inputs object, with ``schema_version`` server-filled.

    Raises:
        TranscriptError: terminal turn is not an assistant JSON object.
        LLMOutputInvalid: parsed JSON fails schema validation or sets a
            forbidden server-controlled key.
    """
    if not transcript:
        raise TranscriptError("transcript has no turns")
    last = transcript[-1]
    if last.role != "assistant":
        raise TranscriptError(
            f"terminal turn must be 'assistant', got {last.role!r}"
        )
    try:
        payload = json.loads(last.content)
    except json.JSONDecodeError as exc:
        raise LLMOutputInvalid(
            f"terminal assistant turn is not valid JSON: {exc}"
        ) from exc
    return validate_llm_output(
        "inputs",
        payload,
        server_filled={"schema_version": "1"},
    )


def run_interview_live(
    transcript: list[TranscriptTurn],
    *,
    model_id: str,
    budget: Budget | None = None,
) -> dict[str, Any]:
    """Live runtime contract — not wired in v1.

    The function performs the runtime gates (allowlist + budget allocation)
    so that tests can verify them, then raises
    :class:`LiveModeNotImplemented`. Wiring an actual provider client is a
    separate, human-merged PR (see roadmap item ``llm-interview-runtime``).

    Raises:
        ModelNotAllowed: ``model_id`` is not in ``docs/models.allowlist.yaml``.
        ModelRoleMismatch: ``model_id`` is allowlisted but not for ``interview``.
        LiveModeNotImplemented: always, after gates pass.
    """
    assert_frontier(model_id, role="interview")
    # Allocate the meter so a future implementation has the budget hook in
    # place; charging is a no-op until the live client lands.
    TokenMeter(budget or Budget.from_env())
    # Touch transcript so static checkers don't flag it as unused.
    if not transcript:
        raise TranscriptError("transcript has no turns")
    raise LiveModeNotImplemented(
        "live Interview mode is not wired in v1; provide a recorded "
        "transcript and use offline mode, or wait for the provider client PR"
    )
