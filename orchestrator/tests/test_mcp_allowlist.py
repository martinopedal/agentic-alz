"""Tests for the MCP server allowlist."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentic_alz.mcp import (
    KNOWN_MODES,
    ModeNotAllowed,
    ServerNotAllowed,
    ToolNotAllowed,
    assert_allowed,
    is_allowed,
    load_allowlist,
    servers_for_mode,
)


# ---------------------------------------------------------------------------
# Loader / shape
# ---------------------------------------------------------------------------
def test_allowlist_loads_and_is_non_empty() -> None:
    allow = load_allowlist()
    assert len(allow) >= 3, "allowlist should contain at least three servers"


def test_allowlist_modes_are_known() -> None:
    for entry in load_allowlist().values():
        assert entry.mode in KNOWN_MODES


def test_write_servers_require_netsec_approval() -> None:
    for entry in load_allowlist().values():
        if entry.mode == "write":
            assert entry.netsec_approval, (
                f"server {entry.id!r} is mode='write' but carries no "
                f"netsec_approval block"
            )
            assert "reviewer" in entry.netsec_approval
            assert "justification" in entry.netsec_approval


def test_github_mcp_apply_path_is_excluded() -> None:
    """`github-mcp` must never be granted tools that can mutate code or CI."""
    allow = load_allowlist()
    if "github-mcp" not in allow:
        pytest.skip("github-mcp not present in this allowlist")
    forbidden = {
        "repos.create_or_update_file",
        "repos.delete_file",
        "git.create_commit",
        "git.update_ref",
        "actions.dispatch_workflow",
        "actions.create_workflow_dispatch",
        "environments.create_or_update",
        "environments.approve_deployment",
        "branches.update_protection",
    }
    overlap = allow["github-mcp"].tools & forbidden
    assert not overlap, (
        f"github-mcp must not be granted apply-path tools, found: {sorted(overlap)}"
    )


# ---------------------------------------------------------------------------
# assert_allowed happy path
# ---------------------------------------------------------------------------
def test_assert_allowed_accepts_known_read_tool() -> None:
    entry = assert_allowed("azure-mcp", "resources.list", "read")
    assert entry.id == "azure-mcp"
    assert entry.mode == "read"


def test_assert_allowed_accepts_known_write_tool() -> None:
    entry = assert_allowed("github-mcp", "issues.create", "write")
    assert entry.id == "github-mcp"


def test_assert_allowed_allows_read_against_write_server() -> None:
    """A read-mode call against a write-mode server is fine."""
    entry = assert_allowed("github-mcp", "checks.list", "read")
    assert entry.id == "github-mcp"


# ---------------------------------------------------------------------------
# assert_allowed rejection paths
# ---------------------------------------------------------------------------
def test_assert_allowed_rejects_unknown_server() -> None:
    with pytest.raises(ServerNotAllowed):
        assert_allowed("evil-mcp", "anything", "read")


def test_assert_allowed_rejects_unknown_tool() -> None:
    with pytest.raises(ToolNotAllowed):
        assert_allowed("azure-mcp", "resources.delete", "read")


def test_assert_allowed_rejects_write_against_read_server() -> None:
    with pytest.raises(ModeNotAllowed):
        assert_allowed("azure-mcp", "resources.list", "write")


def test_assert_allowed_rejects_unknown_mode() -> None:
    with pytest.raises(ValueError, match="unknown mode"):
        assert_allowed("azure-mcp", "resources.list", "delete")


def test_is_allowed_smoke() -> None:
    assert is_allowed("azure-mcp") is True
    assert is_allowed("acme-mcp-9000") is False


def test_servers_for_mode_filters_correctly() -> None:
    write = servers_for_mode("write")
    for entry in write:
        assert entry.mode == "write"
    # Read returns everything (read-mode is a subset of write-mode access).
    read = servers_for_mode("read")
    assert {e.id for e in read} == set(load_allowlist().keys())


# ---------------------------------------------------------------------------
# Rejection of malformed allowlists (override path)
# ---------------------------------------------------------------------------
def test_loader_rejects_wrong_schema_version(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "schema_version: '999'\nservers: []\n", encoding="utf-8"
    )
    load_allowlist.cache_clear()
    try:
        with pytest.raises(ValueError, match="schema_version"):
            load_allowlist(str(bad))
    finally:
        load_allowlist.cache_clear()


def test_loader_rejects_write_without_approval(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "schema_version: '1'\n"
        "servers:\n"
        "  - id: rogue-mcp\n"
        "    transport: stdio\n"
        "    mode: write\n"
        "    tools: ['anything.go']\n",
        encoding="utf-8",
    )
    load_allowlist.cache_clear()
    try:
        with pytest.raises(ValueError, match="netsec_approval"):
            load_allowlist(str(bad))
    finally:
        load_allowlist.cache_clear()


def test_loader_rejects_unknown_mode(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "schema_version: '1'\n"
        "servers:\n"
        "  - id: weird-mcp\n"
        "    transport: stdio\n"
        "    mode: vibes\n"
        "    tools: ['x']\n",
        encoding="utf-8",
    )
    load_allowlist.cache_clear()
    try:
        with pytest.raises(ValueError, match="unknown mode"):
            load_allowlist(str(bad))
    finally:
        load_allowlist.cache_clear()


def test_loader_rejects_empty_tools(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "schema_version: '1'\n"
        "servers:\n"
        "  - id: empty-mcp\n"
        "    transport: stdio\n"
        "    mode: read\n"
        "    tools: []\n",
        encoding="utf-8",
    )
    load_allowlist.cache_clear()
    try:
        with pytest.raises(ValueError, match="tools"):
            load_allowlist(str(bad))
    finally:
        load_allowlist.cache_clear()
