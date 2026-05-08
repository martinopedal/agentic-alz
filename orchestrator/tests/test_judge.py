"""Tests for the build-time multi-model judge."""

from __future__ import annotations

import pytest

from agentic_alz.llm.judge import (
    CriterionVerdict,
    ModelVerdict,
    aggregate,
    from_json,
)
from agentic_alz.llm.models import ModelNotAllowed

RUBRIC = ("cost", "policy", "naming", "version-pinning", "alz-conformance")


def _verdicts(model_id: str, *, fail: tuple[str, ...] = ()) -> ModelVerdict:
    """Build a ModelVerdict where every criterion passes except those in ``fail``."""
    return ModelVerdict(
        model_id=model_id,
        criteria=tuple(
            CriterionVerdict(
                criterion=c,
                verdict="fail" if c in fail else "pass",
                rationale=f"{model_id} on {c}",
            )
            for c in RUBRIC
        ),
    )


def test_unanimous_pass_is_overall_pass() -> None:
    rep = aggregate(
        [
            _verdicts("anthropic/claude-opus-4.7"),
            _verdicts("openai/gpt-5.4"),
            _verdicts("google/gemini-2.5-pro"),
        ],
        rubric=RUBRIC,
    )
    assert rep.overall_pass is True
    assert all(c.passed for c in rep.per_criterion)
    assert rep.required_pass_votes == 3  # default = unanimous


def test_single_dissent_fails_unanimous_threshold() -> None:
    rep = aggregate(
        [
            _verdicts("anthropic/claude-opus-4.7", fail=("cost",)),
            _verdicts("openai/gpt-5.4"),
            _verdicts("google/gemini-2.5-pro"),
        ],
        rubric=RUBRIC,
    )
    assert rep.overall_pass is False
    failing = [c for c in rep.per_criterion if not c.passed]
    assert [c.criterion for c in failing] == ["cost"]
    assert failing[0].dissenting_models == ("anthropic/claude-opus-4.7",)
    assert "FAIL" in rep.summary_markdown
    assert "cost" in rep.summary_markdown


def test_majority_threshold_can_pass_with_dissent() -> None:
    rep = aggregate(
        [
            _verdicts("anthropic/claude-opus-4.7", fail=("cost",)),
            _verdicts("openai/gpt-5.4"),
            _verdicts("google/gemini-2.5-pro"),
        ],
        rubric=RUBRIC,
        required_pass_votes=2,
    )
    assert rep.overall_pass is True


def test_requires_at_least_two_models() -> None:
    with pytest.raises(ValueError, match="at least two models"):
        aggregate([_verdicts("anthropic/claude-opus-4.7")], rubric=RUBRIC)


def test_requires_two_distinct_providers() -> None:
    # Two different Anthropic models is not "consensus".
    with pytest.raises(ValueError, match="two distinct providers"):
        aggregate(
            [
                _verdicts("anthropic/claude-opus-4.7"),
                _verdicts("anthropic/claude-opus-4.6"),
            ],
            rubric=RUBRIC,
        )


def test_rejects_non_allowlisted_model() -> None:
    bogus = ModelVerdict(
        model_id="acme/synthwave-9000",
        criteria=tuple(
            CriterionVerdict(criterion=c, verdict="pass", rationale="x") for c in RUBRIC
        ),
    )
    with pytest.raises(ModelNotAllowed):
        aggregate(
            [_verdicts("anthropic/claude-opus-4.7"), bogus],
            rubric=RUBRIC,
        )


def test_rejects_inconsistent_rubric() -> None:
    bad = ModelVerdict(
        model_id="openai/gpt-5.4",
        criteria=(CriterionVerdict("cost", "pass", "ok"),),
    )
    with pytest.raises(ValueError, match="voted on"):
        aggregate(
            [_verdicts("anthropic/claude-opus-4.7"), bad],
            rubric=RUBRIC,
        )


def test_rejects_duplicate_models() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        aggregate(
            [
                _verdicts("anthropic/claude-opus-4.7"),
                _verdicts("anthropic/claude-opus-4.7"),
            ],
            rubric=RUBRIC,
        )


def test_rejects_invalid_threshold() -> None:
    with pytest.raises(ValueError, match="required_pass_votes"):
        aggregate(
            [_verdicts("anthropic/claude-opus-4.7"), _verdicts("openai/gpt-5.4")],
            rubric=RUBRIC,
            required_pass_votes=99,
        )


def test_rejects_empty_rubric() -> None:
    with pytest.raises(ValueError, match="rubric must be non-empty"):
        aggregate(
            [_verdicts("anthropic/claude-opus-4.7"), _verdicts("openai/gpt-5.4")],
            rubric=(),
        )


def test_criterion_verdict_validates_fields() -> None:
    with pytest.raises(ValueError):
        CriterionVerdict(criterion="cost", verdict="maybe", rationale="x")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        CriterionVerdict(criterion="cost", verdict="pass", rationale="   ")
    with pytest.raises(ValueError):
        CriterionVerdict(criterion="", verdict="pass", rationale="x")


def test_from_json_roundtrip() -> None:
    payload = {
        "rubric": list(RUBRIC),
        "verdicts": [
            {
                "model_id": "anthropic/claude-opus-4.7",
                "criteria": [
                    {"criterion": c, "verdict": "pass", "rationale": "ok"} for c in RUBRIC
                ],
            },
            {
                "model_id": "openai/gpt-5.4",
                "criteria": [
                    {"criterion": c, "verdict": "pass", "rationale": "ok"} for c in RUBRIC
                ],
            },
        ],
    }
    verdicts, rubric = from_json(payload)
    rep = aggregate(verdicts, rubric=rubric)
    assert rep.overall_pass is True
