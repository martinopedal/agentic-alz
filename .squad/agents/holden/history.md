# Holden — History

**Project:** Agentic ALZ — deterministic GitOps pipeline for Azure Landing Zones (ALZ Accelerator + AVM + Terraform), with narrow LLM stages (Interview, Design, Drift Triage, Firewall Composer). Apply is never an LLM action.
**Stack:** Python 3 (orchestrator), Terraform/AVM (templates), OPA Rego (policies), GitHub Actions, MCP, frontier LLMs
**Repo:** martinopedal/agentic-alz
**Lead user:** martinopedal
**Cast at:** 2026-05-12T22:36:05Z

## Core Context

- AGENTS.md (root) is the canonical agent-instruction surface. `.github/copilot-instructions.md` is a 5-line stub pointing at it. `prompts/system/agent-preamble.v1.md` is the runtime mirror. All three carry matching `agent-instructions-version` markers. CI job `lint-instructions` enforces sync.
- Playbooks: `docs/playbooks/0X-*.md` — every non-trivial change picks one (or more) and must satisfy its `## Definition of Done`.
- Generated docs (`docs/generated/`) are auto-rendered by `scripts/gen_docs.py`. NEVER hand-edit. The `docs` workflow fails on any diff.
- Every PR must populate `## Rubberduck`, `## Multi-model judge`, `## Frontier-model attestation`, `## Playbook` sections. Bypass label: `incident`.

## Learnings

(append below — newest at top)

### 2026-05-13: Hiding internal tooling behind maintainer area — squad-hidden directive

**Decision:** Implemented Martin's "squad-hidden-from-public-docs" directive by adding a collapsed README maintainer section, creating docs/maintaining/ subtree, and updating CODEOWNERS. Decision artifact: .squad/decisions/inbox/holden-readme-hide-squad.md.

**Key learnings:**

- **Disambiguating one-liner pattern:** When a term has multiple meanings in a single document (here: "squad" = public GitHub-issue automation vs. internal coordination layer), a single clarifying sentence in the existing bullet is sufficient to prevent conflation. Keeps the source clean and avoids redundant cross-references.

- **Maintainer-area subtree convention:** Establish `docs/maintaining/` as a dedicated home for maintainer-facing docs that are NOT part of the public product surface. This allows future maintainer docs (onboarding, internal runbooks, coordination guides) to have a natural home without polluting the public `docs/` tree or cluttering the README. The convention pairs nicely with `docs/generated/` (auto-rendered) and `docs/playbooks/` (task guidance).

- **CODEOWNERS extension pattern:** When adding new maintainer-only paths, extend CODEOWNERS with a short comment block explaining the category (e.g., "Squad coordination layer — maintainer-only tooling") and then list the paths. Keeps the file self-documenting. Two lines after existing content is sufficient.

- **Collapsed-by-default signal:** A `<details>` block without the `open` attribute clearly signals "this content is supplementary / not part of the main narrative." End users render the page, don't see the section at all, and never feel prompted to click it. Maintainers who know to look for "Maintainer area" in the source will find it and expand.

**Applied in:** This PR implements the full directive: README disambiguator, collapsed details block, new docs/maintaining/squad.md, and CODEOWNERS update. All pure documentation; no behavior change.

### 2026-05-13: Greenlight top 5 roadmap items — re-ranked for gen_docs drift

**Decision:** Greenlighted 5 roadmap items for ROADMAP.md upsert. Re-ranked synthesis top-5 PRs to promote regen-docs-backstop to #1 after coordinator discovered active baseline drift on main (10 stale generated files, cp437 mojibake in cli.md).

**Key learnings:**
- **gen_docs.py codepage trap:** On Windows, Python's `open()` defaults to the system locale (cp437/cp1252), not UTF-8. Any script that generates docs must use `encoding='utf-8'` explicitly. This caused em-dashes (`—`) to render as `ÔÇö` in committed output, creating silent drift that the path-filtered docs.yml workflow never caught.
- **Path-filtered CI creates blind spots:** The docs/generate-and-check workflow only triggers on schemas/, prompts/, policies/, AGENTS.md, and allowlists. If a source-of-truth file outside that filter set changes (e.g., cli.py help text changes, or ROADMAP.md is edited), staleness goes undetected until someone runs `gen_docs.py --check` manually.
- **Schema validation must happen before writing the decision file.** The roadmap schema requires specific patterns for labels (`^[a-z0-9][a-z0-9:_-]*$`), playbook filenames (`^[0-9]{2}-[a-z0-9-]+\.md$`), and IDs. Validating against the schema JSON programmatically is faster and safer than visual inspection.
- **"Supporting infrastructure" can become urgent.** The regen-docs.yml item was originally classified as supporting infrastructure (unranked) in the synthesis. The coordinator's discovery of active drift promoted it to #1. Lesson: always re-evaluate rank when new evidence surfaces.

**Re-ranked top 5:**
1. regen-docs-backstop (was supporting/unranked → promoted to #1)
2. plan-summarizer (was #1 → shifted to #2)
3. rubberduck-generator (was #2 → shifted to #3)
4. shared-pr-opener (was #4 → unchanged at #4)
5. avm-version-bump (was #5 → unchanged at #5)

**Drop file:** .squad/decisions/inbox/holden-roadmap-greenlight-top5.md

### 2026-05-13: Roadmap assignments — Phase 3 agentic features and synthesis

**Synthesis output:** 10-item prioritized agentic roadmap + 3 supporting infrastructure items. 5-member squad roster locked for v1 (Holden, Naomi, Amos, Bobbie, Alex). SRE agent rejected. Docs-always-updated endorsed.

**Assigned items (priority rank):**
4. Drift Triage (rank 4) - Day-2, fill skeleton with agentic triage

**Implementation spec:** Skeleton already exists at `stages/drift_triage.py`. Fill with: (1) read drift detection output (Azure Policy non-compliance, Terraform drift, firewall rule drift), (2) LLM triage + risk classification, (3) open advisory GitHub issue with remediation guidance. Routes through frontier-model allowlist, schema validation, kill-switch.

**Lifecycle position:** Runs post-apply as part of Day-2 monitoring. Never mutates Azure (read-only). Feeds into human triage and remediation workflow.

**Interdependency:** Independent. Can ship after Shared PR Opener (rank 7) is available for issue composition.

**Key architectural decisions finalized:**
- No SRE agent; SRE-shaped stages added incrementally (postmortem draft, compliance snapshot, patch triage)
- Docs-always-updated: two-tier (blocking PR gate + auto-regen safety net on main)
- Lifecycle map: Bootstrap (human) → Interview/Design (agentic-CLI) → Plan (det-CI + advisory) → Apply (det-CI, never agentic) → Day-2 (agentic-CI + CLI)
- Squad roster: Holden (Lead), Naomi, Amos, Bobbie, Alex. No changes for v1.
- AGENTS.md enhancement: Must add evals/replay.py and judge.py to "never edit" list (requires multi-model judge + separate PR)

**Shared insight:** Shared PR Opener (Naomi, rank 7) is the critical architectural enabler. Without it, each candidate rolls its own PR logic, fragmenting rubberduck/judge enforcement.

### 2026-05-13T16:30:00Z: shipped GraphQL Copilot-assign fix + visible-by-default squad framing

- PR #38 (merged): `scripts/squad_bootstrap.py` GraphQL refactor —
  `find_copilot_actor_id()` + `assign_copilot_via_graphql()` +
  `existing_node_id` on `IssuePlan`. Replaces silent-no-op REST
  `add_assignees` for the Copilot bot.
- PR #39 (merged): README split (cloud-agent vs local coord layer),
  new `docs/squad-coordination.md` maintainer guide, CODEOWNERS
  additions for `/.squad/` and `/docs/squad-coordination.md`.
- Decisions ledger entry:
  `graphql-replaceactorsforassignable-is-the-only-path-that-sticks`.
- Cloud agent (PR #37) has picked up issue #32 organically via the
  manual GraphQL assignment from earlier in the session.