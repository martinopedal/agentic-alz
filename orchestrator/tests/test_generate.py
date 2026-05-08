"""Tests for the Generate stage."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_alz.stages.generate import UnsupportedTopology, generate


def test_generate_copies_template(tmp_path: Path, golden_inputs: dict) -> None:
    out = tmp_path / "alz-out"
    manifest = generate(golden_inputs, out)
    assert (out / "main.tf").is_file()
    assert (out / "variables.tf").is_file()
    assert (out / "providers.tf").is_file()
    assert (out / "backend.tf").is_file()
    assert (out / "versions.lock").is_file()
    assert (out / "terraform.tfvars.json").is_file()
    assert manifest["topology"] == "hub-and-spoke"
    assert "main.tf" in manifest["files"]


def test_generate_writes_tfvars_subset(tmp_path: Path, golden_inputs: dict) -> None:
    out = tmp_path / "alz-out"
    generate(golden_inputs, out)
    tfvars = json.loads((out / "terraform.tfvars.json").read_text(encoding="utf-8"))
    # Every variable.tf input is present...
    for k in (
        "org",
        "tenant",
        "management_groups",
        "platform_subscriptions",
        "regions",
        "connectivity",
        "logging",
        "policy_baseline",
        "naming",
        "tags",
    ):
        assert k in tfvars, f"missing {k}"
    # ...and unrelated keys are filtered out (budgets, break_glass).
    assert "budgets" not in tfvars
    assert "break_glass" not in tfvars


def test_generate_rejects_unsupported_topology(tmp_path: Path, golden_inputs: dict) -> None:
    inputs = {**golden_inputs, "connectivity": {**golden_inputs["connectivity"], "topology": "vwan"}}
    with pytest.raises(UnsupportedTopology):
        generate(inputs, tmp_path / "alz-out")
