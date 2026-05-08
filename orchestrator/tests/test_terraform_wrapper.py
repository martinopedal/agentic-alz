"""Tests for the Terraform CLI safety wrapper."""

from __future__ import annotations

import pytest

from agentic_alz.killswitch import KillSwitchEngaged
from agentic_alz.terraform.wrapper import (
    TerraformOperationDenied,
    evaluate,
    require_allowed,
)


@pytest.fixture(autouse=True)
def _ensure_kill_switch_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AGENTIC_ALZ_DISABLED", raising=False)


def test_plan_is_allowed() -> None:
    assert evaluate(["plan", "-out", "tfplan"]).allowed


def test_validate_is_allowed() -> None:
    assert evaluate(["validate"]).allowed


def test_destroy_is_denied_without_override() -> None:
    decision = evaluate(["destroy"])
    assert not decision.allowed
    assert "destructive" in decision.reason


def test_destroy_is_allowed_with_override() -> None:
    assert evaluate(["destroy"], override=True).allowed


def test_state_rm_is_denied_without_override() -> None:
    decision = evaluate(["state", "rm", "module.foo.azurerm_x.y"])
    assert not decision.allowed
    assert "state rm" in decision.reason


def test_state_list_is_allowed() -> None:
    assert evaluate(["state", "list"]).allowed


def test_apply_requires_plan_file() -> None:
    decision = evaluate(["apply"])
    assert not decision.allowed
    assert "saved plan" in decision.reason


def test_apply_rejects_auto_approve() -> None:
    decision = evaluate(["apply", "-auto-approve", "tfplan"])
    assert not decision.allowed
    assert "auto-approve" in decision.reason or "forbidden" in decision.reason


def test_apply_with_plan_file_is_allowed() -> None:
    assert evaluate(["apply", "tfplan"]).allowed


def test_apply_destroy_flag_is_denied() -> None:
    decision = evaluate(["apply", "-destroy", "tfplan"])
    assert not decision.allowed


def test_kill_switch_blocks_evaluation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTIC_ALZ_DISABLED", "true")
    with pytest.raises(KillSwitchEngaged):
        evaluate(["plan"])


def test_require_allowed_raises_on_denial() -> None:
    with pytest.raises(TerraformOperationDenied):
        require_allowed(["destroy"])


def test_require_allowed_passes_when_allowed() -> None:
    require_allowed(["plan"])  # no exception


def test_empty_argv_is_denied() -> None:
    assert not evaluate([]).allowed
