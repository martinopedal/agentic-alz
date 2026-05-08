"""Tests for the frontier-model allowlist."""

from __future__ import annotations

import pytest

from agentic_alz.llm.models import (
    ModelNotAllowed,
    ModelRoleMismatch,
    assert_frontier,
    is_allowed,
    load_allowlist,
    models_for_role,
)


def test_allowlist_loads_and_is_non_empty() -> None:
    allow = load_allowlist()
    assert len(allow) >= 3, "allowlist should contain at least three models"


def test_allowlist_contains_multiple_providers() -> None:
    providers = {e.provider for e in load_allowlist().values()}
    # Diversity is the point of the judge pattern.
    assert len(providers) >= 2


def test_assert_frontier_accepts_allowed_model() -> None:
    entry = assert_frontier("anthropic/claude-opus-4.7", role="design")
    assert entry.provider == "anthropic"


def test_assert_frontier_rejects_unknown_model() -> None:
    with pytest.raises(ModelNotAllowed):
        assert_frontier("openai/gpt-3.5-turbo", role="design")


def test_assert_frontier_rejects_role_mismatch() -> None:
    # Sonnet is allowlisted but not approved for the judge role.
    with pytest.raises(ModelRoleMismatch):
        assert_frontier("anthropic/claude-sonnet-4.6", role="judge")


def test_assert_frontier_rejects_unknown_role() -> None:
    with pytest.raises(ValueError, match="unknown role"):
        assert_frontier("anthropic/claude-opus-4.7", role="vibes")


def test_is_allowed_smoke() -> None:
    assert is_allowed("anthropic/claude-opus-4.7") is True
    assert is_allowed("acme/synthwave-9000") is False


def test_models_for_role_returns_only_approved() -> None:
    judges = models_for_role("judge")
    for entry in judges:
        assert "judge" in entry.roles
    # Sonnet is NOT a judge — make sure it's filtered out.
    assert all(e.id != "anthropic/claude-sonnet-4.6" for e in judges)
