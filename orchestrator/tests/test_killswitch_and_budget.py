"""Tests for kill switch and budget invariants."""

from __future__ import annotations

import pytest

from agentic_alz.budget import Budget, BudgetExceeded, TokenMeter
from agentic_alz.killswitch import KillSwitchEngaged, assert_enabled, is_disabled


def test_kill_switch_default_is_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AGENTIC_ALZ_DISABLED", raising=False)
    assert is_disabled() is False
    assert_enabled()


@pytest.mark.parametrize("value", ["true", "TRUE", "1", "yes", "on"])
def test_kill_switch_truthy_engages(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("AGENTIC_ALZ_DISABLED", value)
    assert is_disabled() is True
    with pytest.raises(KillSwitchEngaged):
        assert_enabled()


@pytest.mark.parametrize("value", ["false", "0", "no", "off", "", "  "])
def test_kill_switch_falsy_disengages(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("AGENTIC_ALZ_DISABLED", value)
    assert is_disabled() is False


def test_token_meter_charges_within_budget() -> None:
    meter = TokenMeter(Budget(token_budget=100))
    meter.charge(40)
    meter.charge(60)
    assert meter.used == 100
    assert meter.remaining == 0


def test_token_meter_rejects_overrun() -> None:
    meter = TokenMeter(Budget(token_budget=100))
    meter.charge(80)
    with pytest.raises(BudgetExceeded):
        meter.charge(21)


def test_token_meter_rejects_negative() -> None:
    meter = TokenMeter(Budget(token_budget=100))
    with pytest.raises(ValueError):
        meter.charge(-1)


def test_budget_from_env_uses_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("LLM_TOKEN_BUDGET", "TOOL_TIMEOUT_S", "APPLY_TIMEOUT_S"):
        monkeypatch.delenv(var, raising=False)
    b = Budget.from_env()
    assert b.token_budget > 0
    assert b.tool_timeout_s > 0
    assert b.apply_timeout_s > 0


def test_budget_from_env_rejects_non_positive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_TOKEN_BUDGET", "0")
    with pytest.raises(ValueError):
        Budget.from_env()


def test_budget_from_env_rejects_non_integer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_TOKEN_BUDGET", "lots")
    with pytest.raises(ValueError):
        Budget.from_env()
