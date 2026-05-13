#!/usr/bin/env python3
"""Roadmap-driven cloud-agent squad bootstrap.

Parses ``ROADMAP.md`` (validated against ``schemas/roadmap.schema.json``) and
upserts one GitHub issue per roadmap item, keyed by an HTML-comment marker on
the issue body so the operation is idempotent across runs.

Items with ``agent_eligible: true`` whose ``depends_on`` are all closed and
which carry no ``human-only`` label are assigned to the GitHub Copilot cloud
agent (``@copilot``); everything else stays unassigned.

The script is intentionally dependency-light: it uses only the standard
library plus PyYAML (already a runtime dep of the orchestrator). HTTP is
plain ``urllib.request`` so the script runs in any minimal CI image.

Usage::

    python scripts/squad_bootstrap.py            # mutate GitHub
    python scripts/squad_bootstrap.py --dry-run  # print plan, mutate nothing

Required environment variables for non-dry-run mode:

* ``GITHUB_TOKEN``  — token with ``issues: write`` on the target repo.
* ``GITHUB_REPOSITORY`` — ``owner/repo`` slug (set automatically in Actions).

The kill switch (``AGENTIC_ALZ_DISABLED``) short-circuits non-dry-run mode
with a non-zero exit, matching the behaviour of every other workflow in the
repo.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
ROADMAP_PATH = REPO_ROOT / "ROADMAP.md"
SCHEMA_PATH = REPO_ROOT / "schemas" / "roadmap.schema.json"

MARKER_PREFIX = "<!-- roadmap-id: "
MARKER_SUFFIX = " -->"
COPILOT_ASSIGNEE = "copilot-swe-agent"  # The Copilot coding agent's REST API login is "copilot-swe-agent". The UI/profile display name is "Copilot", but the API requires the underlying bot login. "Copilot" and "copilot" both fail with HTTP 422 (resource=Issue, field=assignees, code=invalid). Verified 2026-05-13 by direct POST to /repos/<owner>/<repo>/issues/<n>/assignees.
HUMAN_ONLY_LABEL = "human-only"

# H3 heading is one item; fenced ```yaml block underneath holds metadata.
_ITEM_RX = re.compile(
    r"^###\s+(?P<heading>.+?)\s*$\n+```yaml\n(?P<yaml>.*?)\n```",
    re.MULTILINE | re.DOTALL,
)


# ---------------------------------------------------------------------------
# Pure parsing / planning layer (no network — fully unit-testable).
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class RoadmapItem:
    id: str
    title: str
    milestone: str
    summary: str
    acceptance_criteria: tuple[str, ...]
    labels: tuple[str, ...]
    agent_eligible: bool
    depends_on: tuple[str, ...] = ()
    repo: str | None = None
    playbook: str | None = None


@dataclass
class IssuePlan:
    """One planned operation against the GitHub issues API."""

    item: RoadmapItem
    action: str  # "create" | "update" | "noop"
    reason: str
    assign_copilot: bool
    existing_number: int | None = None
    body_diff: tuple[str, str] | None = None  # (old_body_excerpt, new_body_excerpt)


@dataclass
class BootstrapPlan:
    items: list[RoadmapItem]
    issues: list[IssuePlan]
    new_milestones: list[str] = field(default_factory=list)
    new_labels: list[str] = field(default_factory=list)


def parse_roadmap(text: str) -> list[RoadmapItem]:
    """Extract roadmap items from the ROADMAP.md text.

    The parser is positional: the first paragraph between the YAML block and
    the next H3 (or end-of-file) becomes the item's "Context" prose. Items
    are validated structurally here — JSON Schema validation is performed by
    :func:`validate_items` so the parse step stays free of external deps in
    test contexts.
    """
    items: list[RoadmapItem] = []
    matches = list(_ITEM_RX.finditer(text))
    for i, m in enumerate(matches):
        raw = yaml.safe_load(m.group("yaml")) or {}
        if not isinstance(raw, dict):
            raise ValueError(f"Roadmap item under heading {m.group('heading')!r} is not a mapping")
        # Capture prose between this YAML block and the next H3 (or EOF).
        prose_start = m.end()
        prose_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        prose = text[prose_start:prose_end].strip()
        # Strip trailing horizontal rules / heading separators.
        prose = re.sub(r"\n+---\s*$", "", prose).strip()
        # If the YAML omits `summary`, fall back to the first prose paragraph.
        summary = raw.get("summary") or _first_paragraph(prose) or m.group("heading")
        items.append(
            RoadmapItem(
                id=str(raw.get("id", "")),
                title=str(raw.get("title", m.group("heading"))),
                milestone=str(raw.get("milestone", "")),
                summary=summary,
                acceptance_criteria=tuple(raw.get("acceptance_criteria") or ()),
                labels=tuple(raw.get("labels") or ()),
                agent_eligible=bool(raw.get("agent_eligible", False)),
                depends_on=tuple(raw.get("depends_on") or ()),
                repo=raw.get("repo"),
                playbook=raw.get("playbook"),
            )
        )
    return items


def _first_paragraph(prose: str) -> str:
    if not prose:
        return ""
    # Drop leading horizontal-rule / blank lines so a roadmap item that omits
    # `summary` and is followed only by a `---` separator still produces a
    # meaningful fallback (the next non-rule paragraph).
    cleaned_lines = []
    for line in prose.splitlines():
        if not cleaned_lines and (not line.strip() or set(line.strip()) <= {"-"}):
            continue
        cleaned_lines.append(line)
    cleaned = "\n".join(cleaned_lines).strip()
    return cleaned.split("\n\n", 1)[0].strip() if cleaned else ""


def validate_items(items: list[RoadmapItem], schema_path: Path = SCHEMA_PATH) -> None:
    """Validate every parsed item against the JSON Schema.

    Also enforces cross-item invariants the schema cannot express alone:
    unique ids, and ``depends_on`` references resolve to known ids.
    """
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:  # pragma: no cover - dev dep present in CI
        raise RuntimeError(
            "jsonschema is required; install via `pip install -e orchestrator[dev]`"
        ) from exc

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)

    seen: set[str] = set()
    errors: list[str] = []
    for it in items:
        # Re-serialise to dict for the validator (drops None, tuples -> lists).
        as_dict: dict[str, Any] = {
            "id": it.id,
            "title": it.title,
            "milestone": it.milestone,
            "summary": it.summary,
            "acceptance_criteria": list(it.acceptance_criteria),
            "labels": list(it.labels),
            "agent_eligible": it.agent_eligible,
            "depends_on": list(it.depends_on),
        }
        if it.repo is not None:
            as_dict["repo"] = it.repo
        if it.playbook is not None:
            as_dict["playbook"] = it.playbook
        for err in validator.iter_errors(as_dict):
            errors.append(f"{it.id or '<unnamed>'}: {err.message}")
        if it.id in seen:
            errors.append(f"duplicate roadmap id: {it.id!r}")
        seen.add(it.id)

    for it in items:
        for dep in it.depends_on:
            if dep not in seen:
                errors.append(f"{it.id}: depends_on references unknown id {dep!r}")

    if errors:
        raise ValueError("ROADMAP.md validation failed:\n  - " + "\n  - ".join(errors))


def derive_playbook(item: RoadmapItem) -> str:
    """Return the docs/playbooks/ filename that governs this work item.

    Explicit ``item.playbook`` always wins. Otherwise we derive a default
    from labels, in label-precedence order so the most specific surface
    wins. The fallback is ``00-task-router.md`` — which is always safe:
    the router will pick the right surface playbook on the first read.
    """
    if item.playbook:
        return item.playbook
    labels = set(item.labels)
    # Order matters: the first matching rule wins.
    rules: list[tuple[set[str], str]] = [
        ({"area:firewall"}, "07-firewall-lib-exemplar.md"),
        ({"area:ci"}, "08-ci-workflow-change.md"),
        ({"area:llm"}, "04-prompt-or-schema-change.md"),
        ({"area:prompts"}, "04-prompt-or-schema-change.md"),
        ({"area:schemas"}, "04-prompt-or-schema-change.md"),
        ({"area:security"}, "05-policy-change.md"),
        ({"area:terraform"}, "06-iac-template-change.md"),
        ({"area:bicep"}, "06-iac-template-change.md"),
        ({"area:operate"}, "02-bug-fix.md"),
        ({"area:bootstrap"}, "08-ci-workflow-change.md"),
        ({"type:docs"}, "03-doc-only.md"),
    ]
    for required, playbook in rules:
        if required.issubset(labels):
            return playbook
    return "00-task-router.md"


def render_issue_body(item: RoadmapItem) -> str:
    """Deterministic issue body. The marker line is the idempotency key.

    Body structure is stable so drift detection (existing-vs-desired) can be
    a plain string equality check.
    """
    lines = [
        f"{MARKER_PREFIX}{item.id}{MARKER_SUFFIX}",
        "",
        "> This issue is managed by `scripts/squad_bootstrap.py` from "
        "[`ROADMAP.md`](../blob/main/ROADMAP.md). Edit the roadmap, not this body.",
        "",
        "## Context",
        "",
        item.summary.strip(),
        "",
        "## Acceptance criteria",
        "",
    ]
    lines.extend(f"- [ ] {c.strip()}" for c in item.acceptance_criteria)
    lines.extend(
        [
            "",
            "## Metadata",
            "",
            f"- **Roadmap id**: `{item.id}`",
            f"- **Milestone**: {item.milestone}",
            f"- **Labels**: {', '.join(f'`{lbl}`' for lbl in item.labels)}",
            f"- **Agent eligible**: {'yes' if item.agent_eligible else 'no'}",
            f"- **Depends on**: {', '.join(f'`{d}`' for d in item.depends_on) or '—'}",
            f"- **Playbook**: [`docs/playbooks/{derive_playbook(item)}`]"
            f"(../blob/main/docs/playbooks/{derive_playbook(item)})",
        ]
    )
    return "\n".join(lines) + "\n"


def is_assignment_eligible(
    item: RoadmapItem,
    closed_ids: set[str],
    *,
    kill_switch_engaged: bool,
) -> tuple[bool, str]:
    """Return ``(eligible, reason)`` for assigning ``@copilot`` to this item.

    All four conditions must hold:

    1. ``agent_eligible: true`` on the item.
    2. The item has no ``human-only`` label (a label trumps the flag — used
       for emergency takeback without a roadmap edit).
    3. Every entry in ``depends_on`` is in ``closed_ids``.
    4. The kill switch is not engaged.
    """
    if kill_switch_engaged:
        return False, "kill switch engaged (AGENTIC_ALZ_DISABLED)"
    if not item.agent_eligible:
        return False, "agent_eligible: false in ROADMAP.md"
    if HUMAN_ONLY_LABEL in item.labels:
        return False, f"label {HUMAN_ONLY_LABEL!r} pins this item to humans"
    unmet = [d for d in item.depends_on if d not in closed_ids]
    if unmet:
        return False, f"unmet dependencies: {', '.join(unmet)}"
    return True, "eligible"


def plan_operations(
    items: list[RoadmapItem],
    *,
    existing: dict[str, dict[str, Any]],
    closed_ids: set[str],
    existing_milestones: set[str],
    existing_labels: set[str],
    kill_switch_engaged: bool,
) -> BootstrapPlan:
    """Compute the diff between desired roadmap state and observed GitHub state.

    ``existing`` is keyed by roadmap id and yields the GitHub issue dict
    (``number``, ``body``, ``state`` keys at minimum).
    """
    issue_plans: list[IssuePlan] = []
    for item in items:
        desired_body = render_issue_body(item)
        eligible, reason = is_assignment_eligible(
            item, closed_ids, kill_switch_engaged=kill_switch_engaged
        )
        observed = existing.get(item.id)
        if observed is None:
            issue_plans.append(
                IssuePlan(
                    item=item,
                    action="create",
                    reason=f"no existing issue carries marker for {item.id!r}",
                    assign_copilot=eligible,
                )
            )
        elif (observed.get("body") or "").strip() != desired_body.strip():
            issue_plans.append(
                IssuePlan(
                    item=item,
                    action="update",
                    reason="issue body drifted from rendered roadmap",
                    assign_copilot=eligible,
                    existing_number=observed.get("number"),
                    body_diff=(observed.get("body") or "", desired_body),
                )
            )
        else:
            issue_plans.append(
                IssuePlan(
                    item=item,
                    action="noop",
                    reason=reason if not eligible else "up to date",
                    assign_copilot=False,
                    existing_number=observed.get("number"),
                )
            )

    desired_milestones = {it.milestone for it in items}
    desired_labels = {lbl for it in items for lbl in it.labels}
    return BootstrapPlan(
        items=items,
        issues=issue_plans,
        new_milestones=sorted(desired_milestones - existing_milestones),
        new_labels=sorted(desired_labels - existing_labels),
    )


def format_plan(plan: BootstrapPlan) -> str:
    """Human-readable plan, used by ``--dry-run`` and PR comments."""
    lines: list[str] = []
    lines.append(f"# Squad bootstrap plan ({len(plan.issues)} item(s))")
    if plan.new_milestones:
        lines.append("")
        lines.append("## Milestones to create")
        lines.extend(f"- {m}" for m in plan.new_milestones)
    if plan.new_labels:
        lines.append("")
        lines.append("## Labels to create")
        lines.extend(f"- `{lbl}`" for lbl in plan.new_labels)
    lines.append("")
    lines.append("## Issues")
    for ip in plan.issues:
        existing = f" (#{ip.existing_number})" if ip.existing_number else ""
        assign = " → assign @copilot" if ip.assign_copilot else ""
        lines.append(f"- **{ip.action.upper()}** `{ip.item.id}`{existing}: {ip.reason}{assign}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# GitHub HTTP layer (urllib only — no extra deps).
# ---------------------------------------------------------------------------
class GitHubClient:
    """Thin wrapper around the GitHub REST API used by the bootstrap script."""

    API = "https://api.github.com"

    def __init__(self, token: str, repo: str) -> None:
        if "/" not in repo:
            raise ValueError(f"repo must be 'owner/name', got {repo!r}")
        self.token = token
        self.repo = repo

    def _request(self, method: str, path: str, body: dict | None = None) -> Any:
        url = path if path.startswith("http") else f"{self.API}{path}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        req.add_header("User-Agent", "agentic-alz-squad-bootstrap")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as resp:  # noqa: S310 - api.github.com only
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub {method} {path} failed {exc.code}: {detail}") from exc

    def _paginate(self, path: str, params: dict[str, str]) -> list[dict]:
        items: list[dict] = []
        page = 1
        while True:
            q = urllib.parse.urlencode({**params, "page": str(page), "per_page": "100"})
            chunk = self._request("GET", f"{path}?{q}") or []
            if not isinstance(chunk, list) or not chunk:
                break
            items.extend(chunk)
            if len(chunk) < 100:
                break
            page += 1
        return items

    # --- milestones / labels --------------------------------------------------
    def list_milestones(self) -> list[dict]:
        return self._paginate(f"/repos/{self.repo}/milestones", {"state": "all"})

    def create_milestone(self, title: str) -> dict:
        return self._request("POST", f"/repos/{self.repo}/milestones", {"title": title})

    def list_labels(self) -> list[dict]:
        return self._paginate(f"/repos/{self.repo}/labels", {})

    def create_label(self, name: str) -> dict:
        return self._request(
            "POST", f"/repos/{self.repo}/labels", {"name": name, "color": "ededed"}
        )

    # --- issues ---------------------------------------------------------------
    def list_issues(self) -> list[dict]:
        # `state=all` plus `filter=all` for org-managed views; we still filter
        # out PRs (which the issues endpoint also returns).
        items = self._paginate(f"/repos/{self.repo}/issues", {"state": "all"})
        return [i for i in items if "pull_request" not in i]

    def create_issue(
        self,
        *,
        title: str,
        body: str,
        labels: list[str],
        milestone_number: int | None,
        assignees: list[str],
    ) -> dict:
        payload: dict[str, Any] = {"title": title, "body": body, "labels": labels}
        if milestone_number is not None:
            payload["milestone"] = milestone_number
        if assignees:
            payload["assignees"] = assignees
        return self._request("POST", f"/repos/{self.repo}/issues", payload)

    def update_issue(
        self,
        number: int,
        *,
        body: str,
        labels: list[str],
        milestone_number: int | None,
    ) -> dict:
        payload: dict[str, Any] = {"body": body, "labels": labels}
        if milestone_number is not None:
            payload["milestone"] = milestone_number
        return self._request("PATCH", f"/repos/{self.repo}/issues/{number}", payload)

    def add_assignees(self, number: int, assignees: list[str]) -> dict:
        return self._request(
            "POST",
            f"/repos/{self.repo}/issues/{number}/assignees",
            {"assignees": assignees},
        )


# ---------------------------------------------------------------------------
# Issue index helpers
# ---------------------------------------------------------------------------
_MARKER_RX = re.compile(r"<!--\s*roadmap-id:\s*([a-z0-9][a-z0-9-]*[a-z0-9])\s*-->")


def index_existing_issues(issues: list[dict]) -> dict[str, dict]:
    """Index issues by their roadmap-id marker; ignores marker-less issues."""
    out: dict[str, dict] = {}
    for issue in issues:
        body = issue.get("body") or ""
        m = _MARKER_RX.search(body)
        if not m:
            continue
        rid = m.group(1)
        # Prefer the lowest-numbered (oldest) issue if duplicates somehow exist.
        prev = out.get(rid)
        if prev is None or issue.get("number", 0) < prev.get("number", 0):
            out[rid] = issue
    return out


def closed_ids_from(existing: dict[str, dict]) -> set[str]:
    return {rid for rid, issue in existing.items() if issue.get("state") == "closed"}


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def _load_roadmap() -> list[RoadmapItem]:
    items = parse_roadmap(ROADMAP_PATH.read_text(encoding="utf-8"))
    if not items:
        raise ValueError("ROADMAP.md contains no items (no '### …' + ```yaml blocks found)")
    validate_items(items)
    return items


def _kill_switch_engaged() -> bool:
    raw = os.environ.get("AGENTIC_ALZ_DISABLED", "").strip().lower()
    return raw in {"true", "1", "yes", "on"}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan and exit; never mutates GitHub. No token required.",
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("GITHUB_REPOSITORY"),
        help="owner/name slug; defaults to $GITHUB_REPOSITORY.",
    )
    args = parser.parse_args(argv[1:])

    items = _load_roadmap()
    kill_switch = _kill_switch_engaged()

    if args.dry_run:
        # In dry-run we can't talk to GitHub from every developer's laptop, so
        # we synthesise an empty 'existing' map. The plan therefore reads as
        # "everything would be created" — exactly what a reviewer wants to
        # see on the PR that introduces or edits the roadmap.
        plan = plan_operations(
            items,
            existing={},
            closed_ids=set(),
            existing_milestones=set(),
            existing_labels=set(),
            kill_switch_engaged=kill_switch,
        )
        sys.stdout.write(format_plan(plan))
        return 0

    if kill_switch:
        print(
            "ERROR: AGENTIC_ALZ_DISABLED is engaged; refusing to mutate issues.",
            file=sys.stderr,
        )
        return 2

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN not set.", file=sys.stderr)
        return 2
    if not args.repo:
        print("ERROR: --repo or $GITHUB_REPOSITORY required.", file=sys.stderr)
        return 2

    gh = GitHubClient(token, args.repo)
    issues = gh.list_issues()
    existing = index_existing_issues(issues)
    closed_ids = closed_ids_from(existing)
    milestones = {m["title"]: m["number"] for m in gh.list_milestones()}
    labels = {lbl["name"] for lbl in gh.list_labels()}

    plan = plan_operations(
        items,
        existing=existing,
        closed_ids=closed_ids,
        existing_milestones=set(milestones),
        existing_labels=labels,
        kill_switch_engaged=False,
    )
    sys.stdout.write(format_plan(plan))

    # Apply: milestones, then labels, then issues.
    for title in plan.new_milestones:
        ms = gh.create_milestone(title)
        milestones[title] = ms["number"]
        print(f"created milestone: {title}")
    for name in plan.new_labels:
        gh.create_label(name)
        labels.add(name)
        print(f"created label: {name}")

    for ip in plan.issues:
        item = ip.item
        if ip.action == "create":
            # GitHub's POST /repos/{owner}/{repo}/issues endpoint refuses to
            # assign the Copilot coding agent (copilot-swe-agent) at issue
            # creation time with HTTP 422 "cannot be assigned to this issue",
            # even though the same login is accepted by the dedicated
            # POST /repos/{owner}/{repo}/issues/{number}/assignees endpoint.
            # Mirror the UPDATE path: create the issue without assignees, then
            # add @copilot in a second call. This is the same two-step pattern
            # GitHub's own UI uses (REST create + GraphQL replaceActorsForAssignable).
            issue = gh.create_issue(
                title=item.title,
                body=render_issue_body(item),
                labels=list(item.labels),
                milestone_number=milestones.get(item.milestone),
                assignees=[],
            )
            print(f"opened #{issue['number']} {item.id}")
            if ip.assign_copilot:
                try:
                    gh.add_assignees(issue["number"], [COPILOT_ASSIGNEE])
                    print(f"assigned @{COPILOT_ASSIGNEE} to #{issue['number']}")
                except RuntimeError as exc:
                    print(
                        f"::warning::could not assign @copilot to "
                        f"#{issue['number']}: {exc}"
                    )
        elif ip.action == "update" and ip.existing_number is not None:
            gh.update_issue(
                ip.existing_number,
                body=render_issue_body(item),
                labels=list(item.labels),
                milestone_number=milestones.get(item.milestone),
            )
            print(f"updated #{ip.existing_number} {item.id}")
            # Try to add @copilot if newly eligible. Existing assignees are
            # untouched. Failure (e.g. user can't be assigned in this repo)
            # is logged but non-fatal — the human reviewer still sees the
            # issue.
            if ip.assign_copilot:
                try:
                    gh.add_assignees(ip.existing_number, [COPILOT_ASSIGNEE])
                    print(f"assigned @{COPILOT_ASSIGNEE} to #{ip.existing_number}")
                except RuntimeError as exc:
                    print(f"::warning::could not assign @copilot to #{ip.existing_number}: {exc}")
        # noop: nothing to do; eligibility may have changed but the item is
        # already open and pristine — leave humans in control of assignment.
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
