"""Tests for the inputs schema and example golden inputs."""

from __future__ import annotations

import copy

import pytest

from agentic_alz.schema import SchemaValidationError, validate


def test_golden_inputs_validate(golden_inputs: dict) -> None:
    validate("inputs", golden_inputs)


def test_short_code_pattern_enforced(golden_inputs: dict) -> None:
    bad = copy.deepcopy(golden_inputs)
    bad["org"]["short_code"] = "ACME"  # uppercase forbidden
    with pytest.raises(SchemaValidationError):
        validate("inputs", bad)


def test_topology_enum_enforced(golden_inputs: dict) -> None:
    bad = copy.deepcopy(golden_inputs)
    bad["connectivity"]["topology"] = "mesh"
    with pytest.raises(SchemaValidationError):
        validate("inputs", bad)


def test_law_retention_bounds(golden_inputs: dict) -> None:
    bad = copy.deepcopy(golden_inputs)
    bad["logging"]["law_retention_days"] = 10  # below 30
    with pytest.raises(SchemaValidationError):
        validate("inputs", bad)


def test_required_tags_min_three(golden_inputs: dict) -> None:
    bad = copy.deepcopy(golden_inputs)
    bad["tags"]["required"] = ["Owner", "CostCenter"]
    with pytest.raises(SchemaValidationError):
        validate("inputs", bad)


def test_unknown_top_level_key_rejected(golden_inputs: dict) -> None:
    bad = copy.deepcopy(golden_inputs)
    bad["mystery"] = 42
    with pytest.raises(SchemaValidationError):
        validate("inputs", bad)
