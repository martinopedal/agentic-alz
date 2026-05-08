"""MCP server allowlist enforcement.

Every code path that reaches an MCP (Model Context Protocol) tool MUST first
call :func:`assert_allowed`. The allowlist lives at
``docs/mcp.allowlist.yaml`` and is the single source of truth — there is no
in-code default, by design, so adding a server (or moving one to
``mode: write``) requires a PR with NetSec CODEOWNER review.

Rationale: this is the runtime side of the consensus plan's "MCP server
roles" table (``docs/consensus-plan.md §6``). Pairing it with the OPA
policy in ``policies/mcp_allowlist.rego`` means **runtime** stages can only
reach pre-declared tools in pre-declared modes, and **PR-time** review
catches any attempt to widen the surface.

Mirrors the shape of :mod:`agentic_alz.llm.models` deliberately so the two
sensitive surfaces (LLM allowlist and MCP allowlist) feel the same to
callers and to reviewers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

# Permitted modes. Adding a mode is a design change — see
# ``docs/mcp.allowlist.yaml`` and ``docs/consensus-plan.md §6``.
KNOWN_MODES: frozenset[str] = frozenset({"read", "write"})


class ServerNotAllowed(PermissionError):
    """Raised when a non-allowlisted MCP server id is used at runtime."""


class ToolNotAllowed(PermissionError):
    """Raised when a tool not declared in the server's allowlist is used."""


class ModeNotAllowed(PermissionError):
    """Raised when a server is invoked in a mode it is not approved for."""


@dataclass(frozen=True)
class ServerEntry:
    """One row from the MCP allowlist."""

    id: str
    transport: str
    mode: str
    tools: frozenset[str]
    notes: str = ""
    netsec_approval: dict[str, str] = field(default_factory=dict)


def _allowlist_path() -> Path:
    here = Path(__file__).resolve()
    # orchestrator/agentic_alz/mcp/__init__.py -> repo root
    return here.parent.parent.parent.parent / "docs" / "mcp.allowlist.yaml"


@lru_cache(maxsize=1)
def load_allowlist(path: str | None = None) -> dict[str, ServerEntry]:
    """Load and validate the allowlist; cached for the process lifetime.

    Args:
        path: Override the default location (mainly for tests). Cached per
            argument value.

    Raises:
        FileNotFoundError: The allowlist file does not exist.
        ValueError: The file is malformed (wrong ``schema_version``, empty
            ``servers`` list, unknown ``mode``, ``mode: write`` without a
            ``netsec_approval`` block, etc.).
    """
    p = Path(path) if path else _allowlist_path()
    if not p.is_file():
        raise FileNotFoundError(f"mcp allowlist not found: {p}")
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if raw.get("schema_version") != "1":
        raise ValueError("mcp allowlist must have schema_version: '1'")
    entries: dict[str, ServerEntry] = {}
    for row in raw.get("servers", []):
        _require_keys(row, ("id", "transport", "mode", "tools"))
        mode = row["mode"]
        if mode not in KNOWN_MODES:
            raise ValueError(
                f"server {row['id']!r} declares unknown mode {mode!r}; "
                f"known modes are {sorted(KNOWN_MODES)}"
            )
        tools = row["tools"]
        if not isinstance(tools, list) or not tools:
            raise ValueError(
                f"server {row['id']!r} must declare a non-empty tools list"
            )
        approval = row.get("netsec_approval") or {}
        if mode == "write" and not approval:
            # Defence-in-depth: the OPA policy enforces this on every PR,
            # but the runtime check ensures a malformed file at runtime is
            # never silently treated as approved.
            raise ValueError(
                f"server {row['id']!r} declares mode='write' without a "
                f"netsec_approval block; see policies/mcp_allowlist.rego"
            )
        if row["id"] in entries:
            raise ValueError(f"duplicate server id {row['id']!r}")
        entries[row["id"]] = ServerEntry(
            id=row["id"],
            transport=row["transport"],
            mode=mode,
            tools=frozenset(tools),
            notes=row.get("notes", ""),
            netsec_approval=dict(approval),
        )
    if not entries:
        raise ValueError("mcp allowlist is empty")
    return entries


def is_allowed(server_id: str) -> bool:
    """Return True if ``server_id`` appears in the allowlist."""
    return server_id in load_allowlist()


def assert_allowed(server: str, tool: str, mode: str) -> ServerEntry:
    """Raise if ``server``/``tool``/``mode`` is not approved.

    Args:
        server: The exact server id, e.g. ``"azure-mcp"``.
        tool: The exact tool name as listed in the allowlist, e.g.
            ``"resources.list"``.
        mode: ``"read"`` or ``"write"``. The caller declares the mode it
            intends to use; the allowlist's mode is the **maximum** the
            server is approved for. A read-mode call against a write-mode
            server is allowed; a write-mode call against a read-mode server
            raises :class:`ModeNotAllowed`.

    Returns:
        The :class:`ServerEntry` for the server (useful so callers don't
        need to re-look it up).

    Raises:
        ValueError: ``mode`` is not a known mode.
        ServerNotAllowed: ``server`` is not in the allowlist.
        ToolNotAllowed: ``server`` is allowed but ``tool`` is not declared.
        ModeNotAllowed: ``server`` is allowed but only for a narrower mode.
    """
    if mode not in KNOWN_MODES:
        raise ValueError(f"unknown mode {mode!r}; known modes: {sorted(KNOWN_MODES)}")
    allow = load_allowlist()
    entry = allow.get(server)
    if entry is None:
        raise ServerNotAllowed(
            f"mcp server {server!r} is not in the allowlist; "
            f"see docs/mcp.allowlist.yaml"
        )
    if tool not in entry.tools:
        raise ToolNotAllowed(
            f"tool {tool!r} is not declared for server {server!r}; "
            f"approved tools: {sorted(entry.tools)}"
        )
    # Mode check: requested write requires approved write; requested read
    # is fine against either approved mode.
    if mode == "write" and entry.mode != "write":
        raise ModeNotAllowed(
            f"server {server!r} is approved for mode {entry.mode!r}; "
            f"mode='write' requires NetSec CODEOWNER approval — see "
            f"docs/mcp.allowlist.yaml and policies/mcp_allowlist.rego"
        )
    return entry


def servers_for_mode(mode: str) -> list[ServerEntry]:
    """Return all allowlisted servers approved for ``mode``, sorted by id."""
    if mode not in KNOWN_MODES:
        raise ValueError(f"unknown mode {mode!r}")
    if mode == "read":
        # Read-mode is permitted against every entry (write entries can be
        # called read-only too).
        candidates = load_allowlist().values()
    else:
        candidates = (e for e in load_allowlist().values() if e.mode == "write")
    return sorted(candidates, key=lambda e: e.id)


def _require_keys(row: dict[str, Any], keys: tuple[str, ...]) -> None:
    missing = [k for k in keys if k not in row]
    if missing:
        raise ValueError(f"allowlist row missing keys {missing}: {row}")


__all__ = [
    "KNOWN_MODES",
    "ModeNotAllowed",
    "ServerEntry",
    "ServerNotAllowed",
    "ToolNotAllowed",
    "assert_allowed",
    "is_allowed",
    "load_allowlist",
    "servers_for_mode",
]
