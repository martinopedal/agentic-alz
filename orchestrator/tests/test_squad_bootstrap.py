"""Tests for scripts/squad_bootstrap.py.

The bootstrap script lives outside the orchestrator package, so we import it
by file path. Tests cover the pure parsing/eligibility/planning layer; the
GitHub HTTP layer is intentionally not exercised against the network.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "squad_bootstrap.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("squad_bootstrap", SCRIPT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["squad_bootstrap"] = mod
    spec.loader.exec_module(mod)
    return mod


sb = _load_module()


# ---------------------------------------------------------------------------
# parse_roadmap / validate_items
# ---------------------------------------------------------------------------
def test_real_roadmap_parses_and_validates() -> None:
    items = sb.parse_roadmap((REPO_ROOT / "ROADMAP.md").read_text(encoding="utf-8"))
    assert items, "ROADMAP.md should contain at least one item"
    sb.validate_items(items)
    ids = [it.id for it in items]
    assert len(ids) == len(set(ids)), "roadmap ids must be unique"


def test_real_roadmap_apply_stays_human_only() -> None:
    """Apply must never be agent_eligible — invariant from the consensus plan."""
    items = sb.parse_roadmap((REPO_ROOT / "ROADMAP.md").read_text(encoding="utf-8"))
    apply_items = [it for it in items if "apply" in it.id.lower()]
    assert apply_items, "expected at least one apply-related roadmap item"
    for it in apply_items:
        assert not it.agent_eligible, f"{it.id} touches apply — must stay human-only"
        assert sb.HUMAN_ONLY_LABEL in it.labels


def test_parse_minimal_item() -> None:
    text = """\
# Roadmap

### Do the thing

```yaml
id: do-the-thing
title: "Do the thing"
milestone: "Phase X"
labels: [area:test]
agent_eligible: true
acceptance_criteria:
  - "It is done"
```

Some prose context.
"""
    items = sb.parse_roadmap(text)
    assert len(items) == 1
    item = items[0]
    assert item.id == "do-the-thing"
    assert item.agent_eligible is True
    # When summary is omitted, first prose paragraph is used.
    assert "prose context" in item.summary.lower()


def test_validate_rejects_duplicate_ids() -> None:
    items = [
        sb.RoadmapItem(
            id="dup",
            title="A",
            milestone="M",
            summary="x" * 20,
            acceptance_criteria=("do",),
            labels=("area:x",),
            agent_eligible=False,
        ),
        sb.RoadmapItem(
            id="dup",
            title="B",
            milestone="M",
            summary="y" * 20,
            acceptance_criteria=("do",),
            labels=("area:x",),
            agent_eligible=False,
        ),
    ]
    with pytest.raises(ValueError, match="duplicate roadmap id"):
        sb.validate_items(items)


def test_validate_rejects_unknown_dependency() -> None:
    items = [
        sb.RoadmapItem(
            id="a",
            title="A",
            milestone="M",
            summary="x" * 20,
            acceptance_criteria=("do",),
            labels=("area:x",),
            agent_eligible=False,
            depends_on=("ghost",),
        )
    ]
    with pytest.raises(ValueError, match="unknown id"):
        sb.validate_items(items)


# ---------------------------------------------------------------------------
# is_assignment_eligible
# ---------------------------------------------------------------------------
def _item(**kw) -> sb.RoadmapItem:
    defaults = dict(
        id="x",
        title="X",
        milestone="M",
        summary="s" * 20,
        acceptance_criteria=("do",),
        labels=("area:x",),
        agent_eligible=True,
        depends_on=(),
    )
    defaults.update(kw)
    return sb.RoadmapItem(**defaults)


def test_eligible_when_flag_true_no_deps() -> None:
    ok, _ = sb.is_assignment_eligible(_item(), set(), kill_switch_engaged=False)
    assert ok is True


def test_not_eligible_when_flag_false() -> None:
    ok, reason = sb.is_assignment_eligible(
        _item(agent_eligible=False), set(), kill_switch_engaged=False
    )
    assert ok is False
    assert "agent_eligible" in reason


def test_not_eligible_with_human_only_label() -> None:
    ok, reason = sb.is_assignment_eligible(
        _item(labels=("area:x", "human-only")), set(), kill_switch_engaged=False
    )
    assert ok is False
    assert "human-only" in reason


def test_not_eligible_with_open_dependency() -> None:
    ok, reason = sb.is_assignment_eligible(
        _item(depends_on=("a", "b")), {"a"}, kill_switch_engaged=False
    )
    assert ok is False
    assert "b" in reason


def test_eligible_when_all_deps_closed() -> None:
    ok, _ = sb.is_assignment_eligible(
        _item(depends_on=("a", "b")), {"a", "b"}, kill_switch_engaged=False
    )
    assert ok is True


def test_kill_switch_blocks_assignment() -> None:
    ok, reason = sb.is_assignment_eligible(_item(), set(), kill_switch_engaged=True)
    assert ok is False
    assert "kill switch" in reason.lower()


# ---------------------------------------------------------------------------
# render_issue_body / index_existing_issues — idempotency contract
# ---------------------------------------------------------------------------
def test_rendered_body_contains_marker_and_round_trips() -> None:
    item = _item(id="round-trip-id")
    body = sb.render_issue_body(item)
    assert f"<!-- roadmap-id: {item.id} -->" in body
    indexed = sb.index_existing_issues(
        [{"number": 7, "body": body, "state": "open"}]
    )
    assert "round-trip-id" in indexed
    assert indexed["round-trip-id"]["number"] == 7


def test_index_ignores_issues_without_marker() -> None:
    indexed = sb.index_existing_issues(
        [{"number": 1, "body": "no marker here", "state": "open"}]
    )
    assert indexed == {}


def test_index_prefers_oldest_on_duplicate_marker() -> None:
    body = sb.render_issue_body(_item(id="dup-marker"))
    indexed = sb.index_existing_issues(
        [
            {"number": 99, "body": body, "state": "open"},
            {"number": 4, "body": body, "state": "open"},
        ]
    )
    assert indexed["dup-marker"]["number"] == 4


# ---------------------------------------------------------------------------
# derive_playbook / Playbook line in body
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "labels, expected",
    [
        (("area:firewall",), "07-firewall-lib-exemplar.md"),
        (("area:ci",), "08-ci-workflow-change.md"),
        (("area:llm",), "04-prompt-or-schema-change.md"),
        (("area:prompts",), "04-prompt-or-schema-change.md"),
        (("area:schemas",), "04-prompt-or-schema-change.md"),
        (("area:security",), "05-policy-change.md"),
        (("area:terraform",), "06-iac-template-change.md"),
        (("area:bicep",), "06-iac-template-change.md"),
        (("area:bootstrap",), "08-ci-workflow-change.md"),
        (("type:docs",), "03-doc-only.md"),
        (("area:operate",), "02-bug-fix.md"),
        (("unrelated",), "00-task-router.md"),
    ],
)
def test_derive_playbook_from_labels(labels, expected) -> None:
    assert sb.derive_playbook(_item(labels=labels)) == expected


def test_derive_playbook_explicit_overrides_labels() -> None:
    item = _item(labels=("area:firewall",), playbook="01-roadmap-item.md")
    assert sb.derive_playbook(item) == "01-roadmap-item.md"


def test_rendered_body_contains_playbook_line() -> None:
    item = _item(id="pb-test", labels=("area:firewall",))
    body = sb.render_issue_body(item)
    assert "**Playbook**" in body
    assert "07-firewall-lib-exemplar.md" in body


def test_rendered_body_for_unknown_labels_defaults_to_router() -> None:
    body = sb.render_issue_body(_item(id="default-pb", labels=("misc",)))
    assert "00-task-router.md" in body


def test_validate_accepts_explicit_playbook_field() -> None:
    items = [
        _item(
            id="with-pb",
            title="Item with playbook",
            milestone="Phase X",
            summary="A long enough summary " * 3,
            acceptance_criteria=("Verifiable acceptance criterion",),
            playbook="05-policy-change.md",
        )
    ]
    sb.validate_items(items)  # must not raise


def test_validate_rejects_malformed_playbook_field() -> None:
    items = [
        _item(
            id="bad-pb",
            title="Item with bad playbook",
            milestone="Phase X",
            summary="A long enough summary " * 3,
            acceptance_criteria=("Verifiable acceptance criterion",),
            playbook="not-a-playbook.txt",
        )
    ]
    with pytest.raises(ValueError):
        sb.validate_items(items)


# ---------------------------------------------------------------------------
# plan_operations — diff between desired and observed state
# ---------------------------------------------------------------------------
def test_plan_creates_when_no_existing_issue() -> None:
    items = [_item(id="new")]
    plan = sb.plan_operations(
        items,
        existing={},
        closed_ids=set(),
        existing_milestones=set(),
        existing_labels=set(),
        kill_switch_engaged=False,
    )
    assert len(plan.issues) == 1
    assert plan.issues[0].action == "create"
    assert plan.issues[0].assign_copilot is True
    assert "M" in plan.new_milestones
    assert "area:x" in plan.new_labels


def test_plan_noop_when_body_matches() -> None:
    item = _item(id="stable")
    body = sb.render_issue_body(item)
    plan = sb.plan_operations(
        [item],
        existing={"stable": {"number": 12, "body": body, "state": "open"}},
        closed_ids=set(),
        existing_milestones={"M"},
        existing_labels={"area:x"},
        kill_switch_engaged=False,
    )
    assert plan.issues[0].action == "noop"
    assert plan.new_milestones == []
    assert plan.new_labels == []


def test_plan_updates_when_body_drifted() -> None:
    item = _item(id="drift")
    plan = sb.plan_operations(
        [item],
        existing={
            "drift": {
                "number": 33,
                "body": "<!-- roadmap-id: drift -->\nstale content",
                "state": "open",
            }
        },
        closed_ids=set(),
        existing_milestones={"M"},
        existing_labels={"area:x"},
        kill_switch_engaged=False,
    )
    assert plan.issues[0].action == "update"
    assert plan.issues[0].existing_number == 33


def test_plan_blocks_assignment_when_dependency_open() -> None:
    a = _item(id="parent", agent_eligible=False)
    b = _item(id="child", depends_on=("parent",))
    plan = sb.plan_operations(
        [a, b],
        existing={},
        closed_ids=set(),
        existing_milestones=set(),
        existing_labels=set(),
        kill_switch_engaged=False,
    )
    by_id = {ip.item.id: ip for ip in plan.issues}
    assert by_id["child"].assign_copilot is False
    # Once the parent is closed, the child becomes eligible on the next run.
    plan2 = sb.plan_operations(
        [a, b],
        existing={},
        closed_ids={"parent"},
        existing_milestones=set(),
        existing_labels=set(),
        kill_switch_engaged=False,
    )
    by_id2 = {ip.item.id: ip for ip in plan2.issues}
    assert by_id2["child"].assign_copilot is True


def test_format_plan_renders_summary() -> None:
    items = [_item(id="fmt")]
    plan = sb.plan_operations(
        items,
        existing={},
        closed_ids=set(),
        existing_milestones=set(),
        existing_labels=set(),
        kill_switch_engaged=False,
    )
    out = sb.format_plan(plan)
    assert "Squad bootstrap plan" in out
    assert "fmt" in out
    assert "@copilot" in out
