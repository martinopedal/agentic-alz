"""Tests for the post-apply drift cooldown."""

from __future__ import annotations

from pathlib import Path

from agentic_alz.operate.drift_cooldown import DEFAULT_COOLDOWN_S, CooldownStore


def test_cooldown_starts_inactive(tmp_path: Path) -> None:
    store = CooldownStore(tmp_path)
    assert store.is_in_cooldown("alz-platform/eu-west") is False


def test_cooldown_active_immediately_after_apply(tmp_path: Path) -> None:
    store = CooldownStore(tmp_path)
    store.mark_applied("alz-platform/eu-west", now=1000.0)
    assert store.is_in_cooldown("alz-platform/eu-west", now=1000.0)
    assert store.is_in_cooldown("alz-platform/eu-west", now=1000.0 + DEFAULT_COOLDOWN_S - 1)


def test_cooldown_expires(tmp_path: Path) -> None:
    store = CooldownStore(tmp_path)
    store.mark_applied("alz-platform/eu-west", now=1000.0)
    assert not store.is_in_cooldown(
        "alz-platform/eu-west", now=1000.0 + DEFAULT_COOLDOWN_S + 1
    )


def test_cooldown_is_per_state(tmp_path: Path) -> None:
    store = CooldownStore(tmp_path)
    store.mark_applied("alz-platform/eu-west", now=1000.0)
    assert store.is_in_cooldown("alz-platform/eu-west", now=1000.0)
    assert not store.is_in_cooldown("alz-platform/us-east", now=1000.0)


def test_cooldown_handles_slashy_state_id(tmp_path: Path) -> None:
    # Should not write outside the root directory.
    store = CooldownStore(tmp_path)
    store.mark_applied("alz-platform/eu/west")
    files = list(tmp_path.iterdir())
    assert len(files) == 1
    assert files[0].parent == tmp_path
