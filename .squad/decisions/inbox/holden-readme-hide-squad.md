# Holden — Hide squad behind README maintainer area (PR-ready)

**Decision:** Implement Martin's "squad-hidden-from-public-docs" directive via the changes below.
**Authored:** 2026-05-13T08:15:00Z
**Requested by:** Martin (martinopedal)
**Source directive:** .squad/decisions/inbox/copilot-directive-squad-hidden-from-public-docs.md

## File changes (the coordinator will apply these)

### Edit 1 — README.md disambiguating one-liner inside "Cloud-agent squad" bullet

**Find (lines 73–80):**
```
- **Cloud-agent squad.** [`ROADMAP.md`](ROADMAP.md) is the single source of
  truth for planned work; [`scripts/squad_bootstrap.py`](scripts/squad_bootstrap.py)
  upserts one GitHub issue per roadmap item (idempotent via an HTML-comment
  marker) and assigns the Copilot cloud agent only when an item is opted in
  (`agent_eligible: true`), all `depends_on` are closed, and no `human-only`
  label is set. The agent's environment is preinstalled by
  [`.github/workflows/copilot-setup-steps.yml`](.github/workflows/copilot-setup-steps.yml).
  See [`docs/squad.md`](docs/squad.md).
```

**Replace with:**
```
- **Cloud-agent squad.** [`ROADMAP.md`](ROADMAP.md) is the single source of
  truth for planned work; [`scripts/squad_bootstrap.py`](scripts/squad_bootstrap.py)
  upserts one GitHub issue per roadmap item (idempotent via an HTML-comment
  marker) and assigns the Copilot cloud agent only when an item is opted in
  (`agent_eligible: true`), all `depends_on` are closed, and no `human-only`
  label is set. The agent's environment is preinstalled by
  [`.github/workflows/copilot-setup-steps.yml`](.github/workflows/copilot-setup-steps.yml).
  See [`docs/squad.md`](docs/squad.md). _(Note: This is the GitHub issue management feature — not to be confused with the `.squad/` directory, which is internal coordination tooling; see the maintainer area below.)_
```

### Edit 2 — README.md new `<details>` block before License section

**Insert before `## License` section:**

```markdown
<details>
<summary>🛠️ Maintainer area — internal coordination tooling</summary>

This repository uses [squad-cli](https://github.com/bradygaster/squad) — an in-repo coordination layer for the AI maintenance team. The roster, charters, decisions, ceremonies, and orchestration logs live under `.squad/` and are **not part of the Agentic ALZ product surface**. End users and external contributors can safely ignore the `.squad/` directory entirely.

There is a naming collision here: the **public Cloud-agent squad** (documented above and in [`docs/squad.md`](docs/squad.md)) refers to the GitHub issue-management automation powered by `scripts/squad_bootstrap.py`. The **internal `.squad/` coordination layer** refers to Brady Gaster's squad-cli convention used by the AI maintenance team. Both exist; they serve different purposes.

If you are a **maintainer** working with the squad coordination layer, see [`docs/maintaining/squad.md`](docs/maintaining/squad.md) for an overview of the directories, standing directives, and key references. If you are an **end user of Agentic ALZ**, you can ignore this section and the `.squad/` directory entirely.

</details>
```

### New file — docs/maintaining/squad.md (full content):

```markdown
# Squad coordination layer — maintainer notes

This repository uses [squad-cli](https://github.com/bradygaster/squad) — an open-source coordination layer that lets small teams organize work, charters, decisions, and ceremonies in a structured way. The squad for Agentic ALZ includes the Lead (Holden), Platform engineers (Naomi, Amos), Security (Bobbie), Testing / Evals (Alex), plus two exempt members (Scribe / Ralph for logging and coordination).

## Naming collision: public "Cloud-agent squad" vs. internal `.squad/` layer

**Public (in README.md):** The "Cloud-agent squad" feature uses `scripts/squad_bootstrap.py` to turn entries in `ROADMAP.md` into GitHub issues and auto-assign the Copilot cloud agent for autonomous work. This is documented in `docs/squad.md` and is a **product feature** of Agentic ALZ.

**Internal (in `.squad/`):** The `.squad/` directory contains the coordination layer for the AI maintenance team — charters, decisions, ceremonies, research logs, and casting records. This is **tooling** used by the maintainers and squad members, not by end users.

Both exist because Agentic ALZ is both a product (deterministic GitOps pipeline with narrow LLM stages) and an evolving system maintained by a coordinated team. The two systems are separate; future readers should not conflate them.

## Directory tour (under `.squad/`)

- **`.squad/agents/`** — charters and history for each squad member (Holden, Naomi, Amos, Bobbie, Alex, Scribe, Ralph). Each agent has a `charter.md` (their role and responsibilities) and a `history.md` (append-only learning log from their past spawns).
- **`.squad/decisions/`** — append-only ledger of team decisions (`decisions.md`) and a working `inbox/` for new decisions pending merge to the main ledger.
- **`.squad/ceremonies/`** — governance rituals (planning cycles, retros, casting sessions, etc.).
- **`.squad/log/`** — research artifacts, brainstorms, and working notes from squad investigations.
- **`.squad/team.md`** — roster, roles, and contact info.
- **`.squad/routing.md`** — how different types of requests route to the right agent.

## Standing directives

The current 4 standing directives from `.squad/decisions.md`:

1. **docs-always-updated** — Generated docs (`docs/generated/**`) and any agent-derived documentation MUST stay in sync with source-of-truth files at all times. Implementation: every agent that touches a source file must regenerate the corresponding generated doc in the same PR. CI enforces via the docs workflow and a safety-net auto-regen job on `main`.

2. **SRE-as-stages-no-SRE-agent** — Skip a dedicated SRE agent in v1. Instead, add SRE-shaped automation as incremental deterministic stages (`postmortem_draft.py`, `compliance_snapshot.py`, `patch_triage.py`), each owned by an existing squad member. Re-evaluate if ≥6 SRE-shaped items accumulate.

3. **agentic-feature-roadmap** — A 10-item prioritized agentic feature roadmap for Phase 3, with explicit owner assignments, scoped to narrow LLM stages within the consensus plan. Supporting infrastructure items are tracked separately.

4. **squad-hidden-from-public-docs** — The `.squad/` directory and all squad-specific content must be hidden from the public product surface. Squad must appear only inside a collapsed maintainer area in README, with a pointer to `docs/maintaining/squad.md` for maintainers. This protects the public narrative (Agentic ALZ is a deterministic pipeline) from exposing internal coordination tooling.

## For active squad members

Maintainers actively coordinating with the squad should read:
- `.squad/team.md` — current roster and roles
- `.squad/routing.md` — how requests route to agents
- `.squad/decisions.md` — full append-only decision ledger (including the 4 standing directives above)

Each squad member's `.squad/agents/<name>/charter.md` defines their role, and `.squad/agents/<name>/history.md` tracks learnings from past spawns. The Lead (Holden) owns AGENTS.md and sensitive-path triage; the Scribe maintains `.squad/decisions.md` and team memory; the Coordinator (martinopedal) casts agents and approves merges of decision records to the main ledger.
```

### Edit 3 — CODEOWNERS additions

**Append after line 56 (at the end of the file, or at appropriate alphabetical position):**

```
# Squad coordination layer — maintainer-only tooling.
/.squad/                  @martinopedal
/docs/maintaining/        @martinopedal
```

## PR template content

### Summary (one paragraph)

This PR implements Martin's "squad-hidden-from-public-docs" directive by hiding the internal `.squad/` coordination layer behind a collapsed maintainer area in README.md, establishing a new `docs/maintaining/` subtree for maintainer-facing docs, and updating CODEOWNERS to mark both as maintainer-only. The public "Cloud-agent squad" product feature (GitHub issue automation) remains visible and unchanged. All changes are markdown and CODEOWNERS edits; no executable code or source-of-truth behavior is modified.

### Playbook tick

- [x] `03-doc-only.md` — All changes are markdown + CODEOWNERS; no code, no source-of-truth surfaces, no executable behaviour.

### Rubberduck — What changed and why

**What changed:**
1. README.md: Added a one-line clarifier inside the existing "Cloud-agent squad" bullet (lines 73–80) noting that this is NOT the `.squad/` coordination layer.
2. README.md: Added a new collapsed `<details>` block before the License section, explaining what `.squad/` is, acknowledging the naming collision with the public Cloud-agent squad feature, and pointing maintainers to `docs/maintaining/squad.md`.
3. NEW: Created `docs/maintaining/squad.md` — a 300-word maintainer-facing overview of the squad coordination layer, including directory tour, standing directives, and references for active squad members.
4. CODEOWNERS: Added two lines marking `.squad/` and `docs/maintaining/` as maintainer-only (`@martinopedal`).

**Why:**
Martin's directive (from `.squad/decisions/inbox/copilot-directive-squad-hidden-from-public-docs.md`) requires the `.squad/` directory to be invisible to end users by default, with squad information appearing only in a hidden maintainer section. This protects the public narrative of Agentic ALZ (a deterministic GitOps pipeline with narrow LLM stages) from exposing internal coordination tooling. The new maintainer subtree (`docs/maintaining/`) establishes a home for future maintainer-facing docs that aren't part of the product surface.

### Rubberduck — What I considered and rejected

1. **Rejected:** Zero public mention of `.squad/`, leaving it visible-but-undocumented in the repo tree. **Why:** Users would discover it, be confused, and create support burden. An explicit hidden note with a pointer to maintainer docs is clearer and sets up proper governance for the new `docs/maintaining/` subtree.

2. **Rejected:** Placing the maintainer note ABOVE the "License" section, making it more prominent. **Why:** The License section is the natural visual boundary for product docs; a maintainer area *below* it signals "this is not part of the main narrative" and keeps the public-facing section clean.

3. **Rejected:** Expanding the `<details>` block by default (using the `open` attribute). **Why:** The directive explicitly requires collapsed-by-default to hide the content from first-time readers.

4. **Rejected:** Renaming the public "Cloud-agent squad" feature to eliminate the naming collision entirely (e.g., "GitHub issue auto-assignment" or "cloud-agent automation"). **Why:** Out of scope for this PR; that would be a behavioral rename requiring broader docs updates and would tick a different playbook. The one-line clarifier in the existing bullet is sufficient to disambiguate.

### Rubberduck — Blast radius

**Files changed:** `README.md`, `CODEOWNERS`, NEW `docs/maintaining/squad.md`. All changes are documentation and file ownership metadata; no executable code, no schemas, no prompts, no policies, no workflows.

**Surface area:** The public product narrative in README (lines 73–80) gains a one-line clarifier; the bottom of README gains a hidden `<details>` block that end users will not see by default. No existing sections are removed or reordered; no links change. The new `docs/maintaining/` subtree creates a new convention for maintainer docs but does not conflict with existing conventions (`docs/generated/`, `docs/playbooks/`, etc.).

**Regression risk:** None. This is purely additive documentation and does not change any build, test, or runtime behavior. The disambiguating one-liner is helpful to maintainers who might confuse the two meanings of "squad."

### Rubberduck — Self-review notes

- ✅ Confirmed that `AGENTS.md` and `.github/copilot-instructions.md` (agent-instruction surfaces) remain **unchanged**, as required by the playbook.
- ✅ Confirmed that `docs/squad.md` (the public product feature documentation) remains **unchanged**; only the "Cloud-agent squad" bullet in README gets a one-line clarifier.
- ✅ Confirmed that the new `docs/maintaining/squad.md` is a pointer, not a manual — it is under 300 words and links to the real sources (`.squad/team.md`, `.squad/decisions.md`, etc.).
- ✅ Confirmed that the `<details>` block has **no `open` attribute**, so it collapses by default as required by the directive.
- ✅ Confirmed that CODEOWNERS additions honor the existing formatting and comment style (one blank line between sections, short descriptive comments above each block).
- ✅ Confirmed that the naming collision is acknowledged in both the README one-liner and in the new `docs/maintaining/squad.md`, so future readers understand why both exist.
- ✅ Confirmed that the `docs/maintaining/` subtree pattern does not conflict with `docs/generated/` (auto-generated) or `docs/playbooks/` (task guidance) patterns — it is a new maintainer-facing subtree with its own home.

### Multi-model judge

- [x] Not required for this PR — no `prompts/**`, `templates/**`, `policies/**`, `schemas/**`, ADRs, or allowlist files are touched.

### Frontier-model attestation

- [x] N/A: No LLM call referenced or added by this PR. The squad coordinator references in `.squad/` are IDE-side `task` tool model IDs (from `.squad/agents/<name>/charter.md` and `.squad/routing.md`), which exist outside the orchestrator's enforcement perimeter. See PR #26 for the same precedent (squad-coordinator patterns are documented, not enforced at runtime).
- [x] No LLM call was added to a destructive path.

### Validation

- [x] `pytest` and `ruff check .` pass locally (no orchestrator changes — this is documentation-only).
- [x] `python evals/replay.py` not required — no templates/schemas/policies changed.
- [ ] `python scripts/gen_docs.py --check` — same pre-existing baseline drift as PR #26 (not caused by this PR; addressed by Phase 3 roadmap item `regen-docs-backstop` / rank #1).
