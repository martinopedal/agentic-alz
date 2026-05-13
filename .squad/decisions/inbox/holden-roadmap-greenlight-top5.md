# Holden — Greenlight Top 5 Roadmap Items

**Decision:** Greenlight the following 5 items as the next ROADMAP.md additions; route via PR for squad_bootstrap.py upsert.
**Authored:** 2026-05-13T14:22:00Z
**Requested by:** Martin (martinopedal)
**Source:** .squad/log/research/holden-synthesis.md (re-ranked: gen_docs drift fix promoted to #1 per coordinator discovery 2026-05-13).

## Re-ranked top 5 (with one-sentence rationale each)

1. **regen-docs.yml backstop + cross-platform gen_docs.py fix** — Active baseline drift on main (10 stale files, cp437 mojibake) directly violates the "docs always updated" standing directive; must fix before any other agentic feature ships.
2. **Plan Summarizer** — Cheapest high-impact agentic win: LLM prose on every plan PR replaces manual parsing of 800-line plan JSON, zero guardrail surface expansion.
3. **Rubberduck Generator** — Reduces rubberduck.yml check failures from ~30% to ~5% by auto-populating PR template sections, multiplying velocity on every subsequent PR.
4. **Shared PR Opener primitive** — Architectural enabler: without a centralised advisory-PR abstraction, every M/L feature (AVM bumps, drift triage PRs) fragments rubberduck/judge enforcement.
5. **AVM Version-Bump weekly workflow** — Automated dependency freshness catches AVM security patches within a week; uses the Shared PR Opener from #4.

## ROADMAP.md entries (ready to append, schema-validated)

Append under `## Phase 3 — Agentic features (post PR #1)`:

### regen-docs.yml backstop + cross-platform reproducible gen_docs.py

```yaml
id: regen-docs-backstop
title: "Phase 3: regen-docs.yml safety-net workflow + cross-platform gen_docs.py fix"
milestone: "Phase 3 — Agentic features"
labels: [area:ci, area:docs, type:infra]
agent_eligible: true
depends_on: []
playbook: "08-ci-workflow-change.md"
summary: >-
  The docs/generate-and-check CI gate is path-filtered and misses staleness
  when source-of-truth files outside its trigger set change. Additionally,
  gen_docs.py produces cp437 mojibake (ÔÇö instead of em-dash) when run on
  Windows without explicit UTF-8 encoding. This item adds a safety-net
  workflow (regen-docs.yml) that detects drift on every push to main and
  opens a bot-authored PR (never auto-merges), plus fixes gen_docs.py to
  force UTF-8 I/O regardless of locale. Implements Tier 2 of the
  docs-always-updated pattern endorsed by the team.
acceptance_criteria:
  - ".github/workflows/regen-docs.yml runs gen_docs.py --check on every push to main (not path-filtered)"
  - "When drift is detected, workflow opens a PR with the regenerated output and label docs:regen"
  - "Workflow never auto-merges; human review required"
  - "scripts/gen_docs.py opens all files with encoding='utf-8' explicitly (no locale-dependent defaults)"
  - "gen_docs.py --check produces identical output on Ubuntu and Windows runners"
  - "Existing docs/generate-and-check gate is not weakened"
  - "Kill switch (AGENTIC_ALZ_DISABLED) short-circuits the workflow"
```

This is the highest-priority item because active baseline drift on main
violates the docs-always-updated standing directive. The fix is pure CI
plumbing and script hardening — no sensitive-surface changes.

### Plan Summarizer — LLM-authored advisory comment on every plan PR

```yaml
id: plan-summarizer
title: "Phase 3: Plan Summarizer posts LLM-authored advisory comment on plan PRs"
milestone: "Phase 3 — Agentic features"
labels: [area:ci, area:llm, area:terraform]
agent_eligible: true
depends_on: [phase2-plan-workflow]
playbook: "01-roadmap-item.md"
summary: >-
  Adds an advisory step to the plan workflow that reads plan JSON +
  Infracost diff, calls the frontier model via assert_frontier, and posts a
  human-readable summary as a PR comment. The summary covers resource
  counts, cost delta, and any drift-flagged items. This is advisory only —
  it never gates merge and never mutates infrastructure. Replaces manual
  parsing of 800-line plan JSON output.
acceptance_criteria:
  - "New step in plan.yml calls frontier model and posts a PR comment summarising the plan"
  - "Comment includes resource add/change/destroy counts, cost delta from Infracost, and top-3 riskiest changes"
  - "LLM call routes through agentic_alz.llm.models.assert_frontier"
  - "Token budget enforced via agentic_alz.budget"
  - "Comment is advisory only — plan.yml never gates merge on the LLM output"
  - "Deterministic fallback: if LLM call fails, plan workflow still succeeds and posts raw resource counts"
  - "Kill switch (AGENTIC_ALZ_DISABLED) skips the LLM step; plan workflow unaffected"
```

### Rubberduck Generator — auto-populate PR template sections

```yaml
id: rubberduck-generator
title: "Phase 3: Rubberduck Generator auto-populates PR template sections from diff"
milestone: "Phase 3 — Agentic features"
labels: [area:ci, area:llm]
agent_eligible: true
depends_on: [cross-eval-gating]
playbook: "01-roadmap-item.md"
summary: >-
  Extends the PR authoring flow to auto-populate the Rubberduck, Playbook,
  Multi-model judge, and Frontier-model attestation sections of the PR
  template using an LLM that reads the PR diff and playbook metadata. The
  human author reviews and edits before merge; rubberduck.yml still checks
  for unfilled placeholders. Reduces rubberduck check failures from ~30%
  to ~5% by eliminating blank-section mistakes.
acceptance_criteria:
  - "GitHub Action or workflow step reads PR diff and populates Rubberduck sections as a draft PR comment or body edit"
  - "LLM call routes through agentic_alz.llm.models.assert_frontier"
  - "Populated sections are clearly marked as LLM-drafted; human must review before merge"
  - "rubberduck.yml still checks for placeholder tokens — auto-populated content must pass the same gate"
  - "Playbook section is populated by matching changed paths to docs/playbooks/00-task-router.md routing table"
  - "Token budget enforced via agentic_alz.budget"
  - "Kill switch (AGENTIC_ALZ_DISABLED) skips auto-population; manual authoring remains the fallback"
```

### Shared PR Opener — reusable advisory-PR primitive

```yaml
id: shared-pr-opener
title: "Phase 3: Shared PR Opener primitive for advisory PRs with rubberduck pre-fill"
milestone: "Phase 3 — Agentic features"
labels: [area:orchestrator]
agent_eligible: true
depends_on: [phase2-validate-workflow]
playbook: "01-roadmap-item.md"
summary: >-
  Creates a reusable orchestrator module (orchestrator/agentic_alz/github/pr.py)
  that encapsulates the pattern "open an advisory PR with diff, rubberduck
  pre-fill, judge attestation slot, and correct labels." This is the
  architectural enabler for all M/L agentic features that need to open PRs
  (AVM version bumps, drift triage remediation proposals, firewall
  composer output). Without it, each feature rolls its own PR logic and
  fragments rubberduck/judge enforcement. Routes through github-mcp
  PR/issue surface only; never triggers an apply.
acceptance_criteria:
  - "orchestrator/agentic_alz/github/pr.py exposes open_advisory_pr() with typed parameters for diff, title, body template, labels, and reviewer list"
  - "Rubberduck sections are pre-filled from caller-provided metadata; placeholders remain for human review"
  - "MCP calls route through agentic_alz.mcp.assert_allowed; only github-mcp PR/issue tools are used"
  - "PR body includes the idempotency marker pattern (<!-- advisory-pr: {source}-{hash} -->) to prevent duplicate PRs"
  - "Unit tests in orchestrator/tests/test_pr_opener.py cover happy path, duplicate detection, and kill-switch bail-out"
  - "Kill switch (AGENTIC_ALZ_DISABLED) causes open_advisory_pr() to return without opening a PR"
```

### AVM Version-Bump — weekly dependency freshness workflow

```yaml
id: avm-version-bump
title: "Phase 3: AVM Version-Bump weekly workflow opens PRs for outdated AVM pins"
milestone: "Phase 3 — Agentic features"
labels: [area:ci, area:terraform]
agent_eligible: true
depends_on: [shared-pr-opener]
playbook: "08-ci-workflow-change.md"
summary: >-
  Weekly cron workflow queries the AVM module registry for newer versions,
  compares against versions.lock files in templates/, and opens a PR per
  outdated module using the Shared PR Opener primitive. Each PR includes
  the changelog delta and runs the full CI pipeline (fmt, validate, tflint,
  checkov, conftest, plan) before requesting human review. This catches
  AVM security patches within 7 days and keeps dependency freshness
  automated without bypassing the human-merge gate.
acceptance_criteria:
  - ".github/workflows/avm-bump.yml runs weekly (cron) and on workflow_dispatch"
  - "Workflow compares each module source in templates/**/versions.tf against the AVM registry"
  - "Opens one PR per outdated module via shared-pr-opener; PR includes old version, new version, and changelog link"
  - "Full CI pipeline (validate + plan + conftest) runs on the bump PR; policies/avm_pinning.rego validates the new pin"
  - "versions.lock is updated atomically with the version bump"
  - "Workflow never auto-merges; human review + approval required"
  - "Kill switch (AGENTIC_ALZ_DISABLED) short-circuits the workflow"
```

## Per-entry routing notes (for the coordinator)

| # | id | sensitive_paths | playbook | judge_required | codeowners |
|---|---|---|---|---|---|
| 1 | regen-docs-backstop | `.github/workflows/regen-docs.yml` (new), `scripts/gen_docs.py` | `08-ci-workflow-change.md` | No — no prompts/templates/policies/schemas/ADRs/allowlists touched | platform |
| 2 | plan-summarizer | `.github/workflows/plan.yml` (adds step) | `01-roadmap-item.md` + `08-ci-workflow-change.md` | No — advisory PR comment only; LLM output is ephemeral (comment), not persisted to source-of-truth | platform |
| 3 | rubberduck-generator | `.github/workflows/rubberduck.yml` (extends) | `01-roadmap-item.md` + `08-ci-workflow-change.md` | No — LLM output populates PR body sections (ephemeral); human edits before merge | platform |
| 4 | shared-pr-opener | `orchestrator/agentic_alz/github/pr.py` (new) | `01-roadmap-item.md` | No — internal plumbing, no source-of-truth surface | none special |
| 5 | avm-version-bump | `.github/workflows/avm-bump.yml` (new), `templates/**/versions.lock` | `08-ci-workflow-change.md` + `06-iac-template-change.md` | No — version pins are deterministic; avm_pinning.rego validates | platform |

## PR template content (for the coordinator to populate the PR template)

### Summary (one paragraph)

Adds 5 new roadmap items to ROADMAP.md under Phase 3, re-ranked to prioritise
the regen-docs.yml backstop and cross-platform gen_docs.py fix after the
coordinator discovered active baseline drift on main (10 stale generated files,
cp437 mojibake). The remaining four items — Plan Summarizer, Rubberduck
Generator, Shared PR Opener, and AVM Version-Bump — preserve the synthesis
order from .squad/log/research/holden-synthesis.md. All entries conform to
schemas/roadmap.schema.json, carry unique kebab-case IDs, and honour the
existing dependency graph. On merge, squad.yml upserts 5 GitHub issues
via squad_bootstrap.py.

### Playbook tick rationale

The closest existing playbook is `03-doc-only.md` — the change is a markdown
edit to ROADMAP.md with no code changes. However, `03-doc-only.md` does not
strictly cover the squad_bootstrap.py side-effect (issue upsert on merge via
squad.yml). The honest assessment: this is a doc-only edit whose merge trigger
is well-understood CI plumbing, not a novel code path. `03-doc-only.md` is the
best fit. If the team later adds a `11-roadmap-edit.md` playbook, that would
be more precise.

### Rubberduck — What changed and why

Five new ROADMAP.md entries under Phase 3. Re-ranked from the original synthesis
to promote regen-docs-backstop to #1 because the coordinator discovered active
docs drift on main — 10 stale files and cp437 mojibake in cli.md. This drift
directly violates the "docs always updated" standing directive (decisions.md,
2026-05-12). The remaining four items (plan-summarizer, rubberduck-generator,
shared-pr-opener, avm-version-bump) preserve the synthesis dependency order.

### Rubberduck — What I considered and rejected

1. **Rejected promoting a new item into the top 5 to make room for the gen_docs
   fix.** The coordinator's instruction was explicit: swap regen-docs to #1 and
   shift the others down; keep the same pool. Promoting a rank-6+ item (e.g.,
   ALZ Conformance Explainer) would dilute the synthesis and break the
   dependency chain.
2. **Rejected setting all 5 items to agent_eligible: true blindly.** Each item
   was evaluated individually against the AGENTS.md sensitive-paths table and
   the ROADMAP.md preamble constraint. All 5 happen to be eligible because none
   touch the enumerated sensitive surfaces (policies/, prompts/, schemas/,
   allowlists, bootstrap/, apply.yml, firewall-policy/). If any did, I would
   have set false.
3. **Rejected opening 5 raw GitHub issues directly, bypassing squad_bootstrap.py.**
   The canonical path matters: ROADMAP.md is the single source of truth,
   squad_bootstrap.py upserts issues idempotently with `<!-- roadmap-id: {id} -->`
   markers, and the squad.yml workflow gates on schema validation. Bypassing
   this path would create orphan issues that diverge from the roadmap and break
   the dependency-tracking and auto-assignment logic.
4. **Rejected adding regen-docs-backstop as a "supporting infrastructure" item
   instead of a ranked roadmap entry.** The coordinator's discovery elevates it
   from infrastructure to an urgent compliance fix. It deserves first-class
   roadmap tracking with acceptance criteria and dependency management.

### Rubberduck — Blast radius

ROADMAP.md edit triggers squad.yml workflow on merge → upserts 5 GitHub issues.
No production impact. No source-of-truth file touched outside ROADMAP.md itself.
No code changes. No CI workflow changes. No schema, prompt, policy, or allowlist
modifications. The squad.yml dry-run step on the PR will preview the exact
issues that would be created, giving reviewers full visibility before merge.

### Rubberduck — Self-review notes

- **Schema validation:** All 5 entries include every required field per
  schemas/roadmap.schema.json (id, title, milestone, summary,
  acceptance_criteria, labels, agent_eligible). Optional fields (depends_on,
  playbook) included where applicable.
- **Idempotency marker:** Each entry has a unique kebab-case id
  (regen-docs-backstop, plan-summarizer, rubberduck-generator,
  shared-pr-opener, avm-version-bump). No collisions with existing ROADMAP.md
  IDs (checked against all 18 existing entries).
- **Dependency graph:** regen-docs-backstop has no deps (urgent fix).
  plan-summarizer depends on phase2-plan-workflow. rubberduck-generator depends
  on cross-eval-gating. shared-pr-opener depends on phase2-validate-workflow.
  avm-version-bump depends on shared-pr-opener. No circular dependencies.
- **Sensitive-path flags:** Verified against AGENTS.md sensitive-paths table.
  All 5 items touch workflow files or orchestrator code but none touch the
  enumerated must-be-false surfaces.
- **Label patterns:** All labels match the `^[a-z0-9][a-z0-9:_-]*$` pattern
  required by the schema.

### Multi-model judge (will the PR need one)

Not required for this PR. The change is limited to ROADMAP.md — no prompts,
templates, policies, schemas, ADRs, or allowlist files are touched. Per
docs/multi-model-judge.md, the judge is required only for PRs touching
`prompts/**`, `templates/**`, `policies/**`, `schemas/**`, ADRs, or the
model/MCP allowlists. ROADMAP.md is not in that set.

### Frontier-model attestation

- **All LLM calls in this PR go through `assert_frontier`:** N/A — this PR
  contains no code that makes LLM calls. It is a markdown-only edit to
  ROADMAP.md.
- **No new model is introduced:** N/A — no models.allowlist.yaml changes.
  The roadmap entries *describe* future features that will use frontier models,
  but those calls will be implemented and attested in their respective PRs.

## Confirmation against standing directives

1. **docs-always-updated (decisions.md, 2026-05-12):** Honoured. Item #1
   (regen-docs-backstop) exists specifically to close the enforcement gap the
   coordinator discovered. ROADMAP.md is itself a source-of-truth for
   gen_docs.py (renders to docs/generated/roadmap.md), so the PR that appends
   these entries must also regenerate docs/generated/ per the docs-always-updated
   skill.

2. **SRE-as-stages (decisions.md, 2026-05-12):** Honoured. No SRE agent
   introduced. The Drift Triage stage (rank 4 in synthesis, not in this top-5
   batch) remains a pipeline stage, not a separate agent. The top 5 selected
   here are all pipeline stages or CI plumbing, consistent with the "narrow
   LLM stages in deterministic pipeline" philosophy.
