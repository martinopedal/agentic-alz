"""Build-time multi-model consensus (planner + judge pattern).

This module is the **build-time** consensus tool described in the consensus
plan §4 ("Multi-model usage at *build time* (not runtime)"). It is **not** a
runtime safety mechanism; runtime safety still comes from typed schemas,
``terraform plan``, Checkov, Infracost, OPA, and human approval.

How it is used:

1. During PR review of a sensitive artefact (a new prompt revision, a new
   golden template, a new OPA policy, an architectural ADR), N allow-listed
   frontier models are asked to evaluate the candidate against a **fixed
   rubric**. Each model returns a structured PASS/FAIL per criterion plus a
   one-sentence rationale.
2. The aggregator in this module collects those structured verdicts (it does
   **not** call the models itself — that is the caller's responsibility, so
   tests stay deterministic) and produces a typed :class:`ConsensusReport`.
3. The CI gate fails the PR if any criterion has fewer than the configured
   number of PASS votes (default: unanimous), surfacing the failing criteria
   and dissenting models in the PR comment. There is no automatic retry and
   no "majority wins on safety" — any FAIL escalates to a human reviewer.

Critically, this module is **deterministic** given its inputs, so the same
N verdicts always produce the same report. The non-determinism (and the
cost) lives in the caller that fans out to the models.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

from .models import KNOWN_ROLES, assert_frontier

Verdict = Literal["pass", "fail"]


@dataclass(frozen=True)
class CriterionVerdict:
    """One model's verdict for one rubric criterion."""

    criterion: str
    verdict: Verdict
    rationale: str

    def __post_init__(self) -> None:
        if self.verdict not in ("pass", "fail"):
            raise ValueError(f"verdict must be 'pass' or 'fail', got {self.verdict!r}")
        if not self.rationale or not self.rationale.strip():
            raise ValueError("rationale must be non-empty")
        if not self.criterion or not self.criterion.strip():
            raise ValueError("criterion must be non-empty")


@dataclass(frozen=True)
class ModelVerdict:
    """All criterion verdicts from a single model."""

    model_id: str
    criteria: tuple[CriterionVerdict, ...]


@dataclass(frozen=True)
class CriterionResult:
    """Aggregated outcome for one criterion across all models."""

    criterion: str
    pass_votes: int
    fail_votes: int
    dissenting_models: tuple[str, ...]
    passed: bool


@dataclass(frozen=True)
class ConsensusReport:
    """Output of :func:`aggregate`."""

    rubric: tuple[str, ...]
    models: tuple[str, ...]
    required_pass_votes: int
    per_criterion: tuple[CriterionResult, ...]
    overall_pass: bool
    summary_markdown: str = field(default="")


def aggregate(
    verdicts: Sequence[ModelVerdict],
    *,
    rubric: Sequence[str],
    required_pass_votes: int | None = None,
    role: str = "judge",
) -> ConsensusReport:
    """Aggregate per-model verdicts into a consensus report.

    Args:
        verdicts: One :class:`ModelVerdict` per participating model. Must
            contain at least two distinct allowlisted models — single-model
            "consensus" is a contradiction in terms.
        rubric: Ordered list of criteria the models were asked about. Each
            model must have voted on every criterion exactly once.
        required_pass_votes: Threshold for a criterion to be considered
            passed. Defaults to **unanimity** (``len(verdicts)``). A safer
            default than majority because the goal is to surface
            disagreement, not paper over it.
        role: The pipeline role (defaults to ``"judge"``); each model id is
            cross-checked against the allowlist for this role.

    Returns:
        A :class:`ConsensusReport`. ``overall_pass`` is True iff every
        criterion meets ``required_pass_votes``.

    Raises:
        ValueError: rubric/verdicts are inconsistent, fewer than two models,
            or a model voted on the wrong criteria.
        ModelNotAllowed / ModelRoleMismatch: any model is not allowlisted.
    """
    if role not in KNOWN_ROLES:
        raise ValueError(f"unknown role {role!r}")
    if len(verdicts) < 2:
        raise ValueError("multi-model consensus requires at least two models")
    if len(rubric) == 0:
        raise ValueError("rubric must be non-empty")
    if len(set(rubric)) != len(rubric):
        raise ValueError("rubric criteria must be unique")

    seen_ids: set[str] = set()
    for mv in verdicts:
        if mv.model_id in seen_ids:
            raise ValueError(f"duplicate model id in verdicts: {mv.model_id}")
        seen_ids.add(mv.model_id)
        # Will raise ModelNotAllowed / ModelRoleMismatch as appropriate.
        assert_frontier(mv.model_id, role=role)
        # Each model must vote on every criterion, exactly once.
        voted = [cv.criterion for cv in mv.criteria]
        if sorted(voted) != sorted(rubric):
            raise ValueError(
                f"model {mv.model_id!r} voted on {sorted(voted)} but rubric is "
                f"{sorted(rubric)}"
            )

    if len({mv.model_id.split("/", 1)[0] for mv in verdicts}) < 2:
        # Diversity check: at least two distinct providers must be present.
        # Cross-lab diversity is the whole point of the judge pattern.
        raise ValueError(
            "judge requires verdicts from at least two distinct providers "
            "(e.g. anthropic + openai); single-provider consensus is rejected"
        )

    threshold = required_pass_votes if required_pass_votes is not None else len(verdicts)
    if not 1 <= threshold <= len(verdicts):
        raise ValueError(
            f"required_pass_votes must be in 1..{len(verdicts)}, got {threshold}"
        )

    per_criterion: list[CriterionResult] = []
    for crit in rubric:
        pass_votes = 0
        fail_votes = 0
        dissenters: list[str] = []
        for mv in verdicts:
            cv = next(c for c in mv.criteria if c.criterion == crit)
            if cv.verdict == "pass":
                pass_votes += 1
            else:
                fail_votes += 1
                dissenters.append(mv.model_id)
        per_criterion.append(
            CriterionResult(
                criterion=crit,
                pass_votes=pass_votes,
                fail_votes=fail_votes,
                dissenting_models=tuple(sorted(dissenters)),
                passed=pass_votes >= threshold,
            )
        )

    overall = all(c.passed for c in per_criterion)
    summary = _render_markdown(
        models=[mv.model_id for mv in verdicts],
        threshold=threshold,
        results=per_criterion,
        overall=overall,
        verdicts=verdicts,
    )
    return ConsensusReport(
        rubric=tuple(rubric),
        models=tuple(sorted(mv.model_id for mv in verdicts)),
        required_pass_votes=threshold,
        per_criterion=tuple(per_criterion),
        overall_pass=overall,
        summary_markdown=summary,
    )


def _render_markdown(
    *,
    models: list[str],
    threshold: int,
    results: list[CriterionResult],
    overall: bool,
    verdicts: Sequence[ModelVerdict],
) -> str:
    lines: list[str] = []
    status = "✅ PASS" if overall else "❌ FAIL — human review required"
    lines.append(f"## Multi-model consensus — {status}")
    lines.append("")
    lines.append(f"- Models: {', '.join(sorted(models))}")
    lines.append(f"- Required pass votes per criterion: **{threshold} / {len(models)}**")
    lines.append("")
    lines.append("| Criterion | Pass | Fail | Outcome | Dissenters |")
    lines.append("| --- | ---: | ---: | --- | --- |")
    for r in results:
        outcome = "✅" if r.passed else "❌"
        dissent = ", ".join(r.dissenting_models) if r.dissenting_models else "—"
        lines.append(
            f"| {r.criterion} | {r.pass_votes} | {r.fail_votes} | {outcome} | {dissent} |"
        )
    if not overall:
        lines.append("")
        lines.append("### Dissent rationales")
        for r in results:
            if r.passed:
                continue
            lines.append(f"- **{r.criterion}**")
            for mv in verdicts:
                cv = next(c for c in mv.criteria if c.criterion == r.criterion)
                if cv.verdict == "fail":
                    lines.append(f"  - `{mv.model_id}`: {cv.rationale}")
    return "\n".join(lines) + "\n"


def from_json(payload: dict[str, Any]) -> tuple[list[ModelVerdict], list[str]]:
    """Parse a JSON document into ``(verdicts, rubric)``.

    Expected shape::

        {
          "rubric": ["cost", "policy", ...],
          "verdicts": [
            {
              "model_id": "anthropic/claude-opus-4.7",
              "criteria": [
                {"criterion": "cost", "verdict": "pass", "rationale": "..."},
                ...
              ]
            },
            ...
          ]
        }
    """
    if not isinstance(payload, dict):
        raise ValueError("judge JSON must be an object")
    rubric = list(payload.get("rubric") or [])
    raw_verdicts = payload.get("verdicts") or []
    if not isinstance(raw_verdicts, list):
        raise ValueError("verdicts must be a list")
    out: list[ModelVerdict] = []
    for row in raw_verdicts:
        if not isinstance(row, dict):
            raise ValueError("each verdict must be an object")
        criteria = tuple(
            CriterionVerdict(
                criterion=c["criterion"],
                verdict=c["verdict"],
                rationale=c["rationale"],
            )
            for c in row.get("criteria", [])
        )
        out.append(ModelVerdict(model_id=row["model_id"], criteria=criteria))
    return out, rubric
