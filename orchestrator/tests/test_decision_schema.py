"""Round-trip tests for `schemas/decision.schema.json`.

Each architectural decision touching a sensitive surface produces a
`decision/<id>/decision.json` validated by this schema (per
`docs/playbooks/10-research-and-decide.md`). The schema is the typed
contract; this test asserts a minimal valid example accepts and that
the obvious mis-shapes are rejected.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "decision.schema.json"


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def minimal_decision() -> dict:
    return {
        "schema_version": "1",
        "id": "iac-flavour-pick",
        "title": "Pick the IaC flavour for v1",
        "problem": "We must choose between Terraform-only and Terraform + Bicep parity for v1; getting it wrong costs a refactor.",
        "options": [
            {"id": "O-001", "summary": "Terraform only; Bicep deferred."},
            {
                "id": "O-002",
                "summary": "Terraform + Bicep peers via flavour selector.",
                "rejected_reason": "Doubles policy surface area for v1.",
            },
        ],
        "criteria": [
            {"id": "C-001", "question": "Does this preserve AVM pinning across flavours?"}
        ],
        "verdicts": [
            {
                "model_id": "anthropic/claude-opus-4.7",
                "provider": "anthropic",
                "chosen_option": "O-001",
                "scores": [
                    {
                        "criterion": "C-001",
                        "verdict": "pass",
                        "rationale": "AVM pinning is unchanged for the Terraform-only path.",
                    }
                ],
            },
            {
                "model_id": "openai/gpt-5.4",
                "provider": "openai",
                "chosen_option": "O-001",
                "scores": [
                    {
                        "criterion": "C-001",
                        "verdict": "pass",
                        "rationale": "No new module sources are introduced; existing rego still applies.",
                    }
                ],
            },
        ],
        "outcome": {
            "chosen_option": "O-001",
            "consensus": "unanimous",
            "rationale": "Both providers PASS C-001 and choose the same option; no dissent recorded.",
        },
        "adr": {"path": "docs/adr/0001-iac-flavour.md"},
    }


def test_minimal_decision_validates(schema, minimal_decision) -> None:
    Draft202012Validator(schema).validate(minimal_decision)


def test_rejects_single_provider(schema, minimal_decision) -> None:
    bad = copy.deepcopy(minimal_decision)
    # Two verdicts but same provider — the cross-provider invariant is
    # enforced at runtime by `agentic_alz.llm.judge.aggregate`; here we
    # at least ensure the schema requires >= 2 verdicts so the runtime
    # check has something to operate on.
    bad["verdicts"] = bad["verdicts"][:1]
    errors = list(Draft202012Validator(schema).iter_errors(bad))
    assert errors, "schema should require at least two verdicts"


def test_rejects_unknown_field(schema, minimal_decision) -> None:
    bad = copy.deepcopy(minimal_decision)
    bad["mystery"] = "extra"
    errors = list(Draft202012Validator(schema).iter_errors(bad))
    assert errors, "schema should be additionalProperties: false at root"


def test_rejects_malformed_option_id(schema, minimal_decision) -> None:
    bad = copy.deepcopy(minimal_decision)
    bad["options"][0]["id"] = "Option-1"
    errors = list(Draft202012Validator(schema).iter_errors(bad))
    assert errors


def test_rejects_non_adr_path(schema, minimal_decision) -> None:
    bad = copy.deepcopy(minimal_decision)
    bad["adr"]["path"] = "README.md"
    errors = list(Draft202012Validator(schema).iter_errors(bad))
    assert errors


def test_rejects_non_pass_fail_verdict(schema, minimal_decision) -> None:
    bad = copy.deepcopy(minimal_decision)
    bad["verdicts"][0]["scores"][0]["verdict"] = "maybe"
    errors = list(Draft202012Validator(schema).iter_errors(bad))
    assert errors


def test_rejects_consensus_outside_enum(schema, minimal_decision) -> None:
    bad = copy.deepcopy(minimal_decision)
    bad["outcome"]["consensus"] = "plurality"
    errors = list(Draft202012Validator(schema).iter_errors(bad))
    assert errors
