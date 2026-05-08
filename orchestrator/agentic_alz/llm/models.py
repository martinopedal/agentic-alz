"""Frontier-model allowlist enforcement.

Every code path that issues an LLM call MUST first call
:func:`assert_frontier`. The allowlist lives at ``docs/models.allowlist.yaml``
and is the single source of truth — there is no in-code default, by design,
so adding a model requires a PR with NetSec + platform-team review.

Rationale: this is the runtime side of the consensus plan's "only frontier
models" commitment. Pairing it with the build-time judge in
:mod:`agentic_alz.llm.judge` means **runtime** stages choose a single
allow-listed model per call, while **PR-time** review uses the judge to
cross-check N allow-listed models against a fixed rubric.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

# Stages that may legitimately call an LLM. Adding a stage here is a design
# change — see docs/consensus-plan.md §4.
KNOWN_ROLES: frozenset[str] = frozenset(
    {
        "interview",
        "design",
        "drift_triage",
        "firewall_compose",
        "judge",
    }
)


class ModelNotAllowed(PermissionError):
    """Raised when a non-allowlisted model id is used at runtime."""


class ModelRoleMismatch(PermissionError):
    """Raised when an allowlisted model is used outside its approved roles."""


@dataclass(frozen=True)
class ModelEntry:
    """One row from the allowlist."""

    id: str
    provider: str
    family: str
    roles: frozenset[str]
    notes: str = ""


def _allowlist_path() -> Path:
    here = Path(__file__).resolve()
    # orchestrator/agentic_alz/llm/models.py -> repo root
    return here.parent.parent.parent.parent / "docs" / "models.allowlist.yaml"


@lru_cache(maxsize=1)
def load_allowlist(path: str | None = None) -> dict[str, ModelEntry]:
    """Load and validate the allowlist; cached for the process lifetime.

    Args:
        path: Override the default location (mainly for tests). Cached per
            argument value.
    """
    p = Path(path) if path else _allowlist_path()
    if not p.is_file():
        raise FileNotFoundError(f"model allowlist not found: {p}")
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if raw.get("schema_version") != "1":
        raise ValueError("model allowlist must have schema_version: '1'")
    entries: dict[str, ModelEntry] = {}
    for row in raw.get("models", []):
        _require_keys(row, ("id", "provider", "family", "role"))
        roles = frozenset(row["role"])
        unknown = roles - KNOWN_ROLES
        if unknown:
            raise ValueError(
                f"model {row['id']!r} declares unknown roles {sorted(unknown)}; "
                f"known roles are {sorted(KNOWN_ROLES)}"
            )
        entries[row["id"]] = ModelEntry(
            id=row["id"],
            provider=row["provider"],
            family=row["family"],
            roles=roles,
            notes=row.get("notes", ""),
        )
    if not entries:
        raise ValueError("model allowlist is empty")
    return entries


def is_allowed(model_id: str) -> bool:
    """Return True if ``model_id`` appears in the allowlist."""
    return model_id in load_allowlist()


def assert_frontier(model_id: str, *, role: str) -> ModelEntry:
    """Raise if ``model_id`` is not allowlisted for ``role``.

    Args:
        model_id: The exact provider-prefixed id, e.g.
            ``"anthropic/claude-opus-4.7"``.
        role: The pipeline stage requesting the call.

    Returns:
        The :class:`ModelEntry` for the model (useful so callers don't need
        to re-look it up).

    Raises:
        ValueError: ``role`` is not a known stage.
        ModelNotAllowed: ``model_id`` is not in the allowlist.
        ModelRoleMismatch: ``model_id`` is allowlisted but not for ``role``.
    """
    if role not in KNOWN_ROLES:
        raise ValueError(f"unknown role {role!r}; known roles: {sorted(KNOWN_ROLES)}")
    allow = load_allowlist()
    entry = allow.get(model_id)
    if entry is None:
        raise ModelNotAllowed(
            f"model {model_id!r} is not in the frontier allowlist; "
            f"see docs/models.allowlist.yaml"
        )
    if role not in entry.roles:
        raise ModelRoleMismatch(
            f"model {model_id!r} is allowlisted but not for role {role!r}; "
            f"approved roles: {sorted(entry.roles)}"
        )
    return entry


def models_for_role(role: str) -> list[ModelEntry]:
    """Return all allowlisted models approved for ``role``, sorted by id."""
    if role not in KNOWN_ROLES:
        raise ValueError(f"unknown role {role!r}")
    return sorted(
        (e for e in load_allowlist().values() if role in e.roles),
        key=lambda e: e.id,
    )


def _require_keys(row: dict[str, Any], keys: tuple[str, ...]) -> None:
    missing = [k for k in keys if k not in row]
    if missing:
        raise ValueError(f"allowlist row missing keys {missing}: {row}")
