"""Structural tests for `AGENTS.md`, `.github/copilot-instructions.md`,
`prompts/system/agent-preamble.v1.md`, and the `docs/playbooks/`
collection. Mirror of the `ci / lint-instructions` job — the test must
fail in the same way CI fails so a contributor sees the problem locally.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PLAYBOOKS_DIR = REPO_ROOT / "docs" / "playbooks"
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"

CANONICAL_MARKER = "<!-- agent-instructions-canonical-source: AGENTS.md -->"
VERSION_RX = re.compile(r"<!--\s*agent-instructions-version:\s*(v\d+)\s*-->")
PLAYBOOK_NAME_RX = re.compile(r"^([0-9]{2})-[a-z0-9-]+\.md$")
REQUIRED_H2 = ("## Triggers", "## Definition of Done", "## References")

AGENT_SURFACES = [
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / ".github" / "copilot-instructions.md",
    REPO_ROOT / "prompts" / "system" / "agent-preamble.v1.md",
]


def _workflow_stems() -> set[str]:
    return {p.stem for p in WORKFLOWS_DIR.glob("*.yml")}


@pytest.mark.parametrize("path", AGENT_SURFACES)
def test_agent_surface_has_canonical_marker(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert CANONICAL_MARKER in text, f"{path} missing canonical-source marker"


def test_agent_surfaces_share_one_version() -> None:
    versions = set()
    for p in AGENT_SURFACES:
        m = VERSION_RX.search(p.read_text(encoding="utf-8"))
        assert m is not None, f"{p} missing agent-instructions-version marker"
        versions.add(m.group(1))
    assert len(versions) == 1, f"agent surfaces disagree on version: {versions}"


def test_pr_template_carries_required_sections() -> None:
    tpl = (REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md").read_text(encoding="utf-8")
    for h in ("## Playbook", "## Rubberduck", "## Multi-model judge", "## Frontier-model attestation"):
        assert h in tpl, f"PR template missing required section: {h!r}"


def test_router_and_ten_surface_playbooks_exist() -> None:
    found = sorted(
        p.name for p in PLAYBOOKS_DIR.glob("*.md") if PLAYBOOK_NAME_RX.match(p.name)
    )
    ids: set[str] = set()
    for n in found:
        m = PLAYBOOK_NAME_RX.match(n)
        assert m is not None  # filtered above
        ids.add(m.group(1))
    assert ids >= {f"{i:02d}" for i in range(0, 11)}, f"missing playbook ids; have {ids}"


@pytest.mark.parametrize(
    "path",
    sorted(p for p in PLAYBOOKS_DIR.glob("*.md") if PLAYBOOK_NAME_RX.match(p.name)),
    ids=lambda p: p.name,
)
def test_playbook_structure(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for h in REQUIRED_H2:
        assert h in text, f"{path.name}: missing required heading {h!r}"
    # References block must list at least three URLs.
    ref = re.search(r"^##\s+References\s*\n(.+?)\Z", text, re.DOTALL | re.MULTILINE)
    assert ref is not None, f"{path.name}: missing ## References block"
    urls = re.findall(r"https?://\S+", ref.group(1))
    assert len(urls) >= 3, f"{path.name}: References must include >= 3 URLs (found {len(urls)})"
    # Definition of Done must reference at least one real CI workflow.
    workflows = _workflow_stems()
    ci_ref_rx = re.compile(
        r"`(" + "|".join(re.escape(w) for w in workflows) + r")\s*/\s*[^`]+`"
    )
    dod = re.search(
        r"^##\s+Definition of Done\s*\n(.+?)(?=^##\s|\Z)",
        text,
        re.DOTALL | re.MULTILINE,
    )
    assert dod is not None
    assert ci_ref_rx.findall(dod.group(1)), (
        f"{path.name}: Definition of Done must reference at least one workflow "
        f"using the `<workflow-stem> / <job>` convention"
    )
