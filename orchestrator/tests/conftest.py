from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def golden_inputs_path(repo_root: Path) -> Path:
    return repo_root / "evals" / "golden" / "hns-minimal" / "inputs.yaml"


@pytest.fixture
def golden_inputs(golden_inputs_path: Path) -> dict:
    return yaml.safe_load(golden_inputs_path.read_text(encoding="utf-8"))


@pytest.fixture
def sample_plan_json() -> dict:
    """A minimal `terraform show -json` plan with one of each tracked action."""
    return json.loads((Path(__file__).parent / "data" / "plan.sample.json").read_text())
