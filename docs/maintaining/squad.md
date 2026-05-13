# Squad coordination layer — maintainer notes

This repository uses [squad-cli](https://github.com/bradygaster/squad) — an
open-source coordination layer that lets small teams organize work, charters,
decisions, and ceremonies in a structured way. The squad for Agentic ALZ
includes the Lead (Holden), Platform engineers (Naomi, Amos), Security
(Bobbie), Testing / Evals (Alex), plus two exempt members (Scribe and Ralph
for logging and continuous coordination).

## Naming collision: public "Cloud-agent squad" vs. internal `.squad/` layer

**Public (in [`README.md`](../../README.md)):** The "Cloud-agent squad"
feature uses [`scripts/squad_bootstrap.py`](../../scripts/squad_bootstrap.py)
to turn entries in [`ROADMAP.md`](../../ROADMAP.md) into GitHub issues and
auto-assign the Copilot cloud agent for autonomous work. This is documented
in [`docs/squad.md`](../squad.md) and is a **product feature** of Agentic
ALZ.

**Internal (in `.squad/`):** The `.squad/` directory contains the coordination
layer for the AI maintenance team — charters, decisions, ceremonies, research
logs, and casting records. This is **tooling** used by maintainers and squad
members, not by end users.

Both exist because Agentic ALZ is both a product (deterministic GitOps
pipeline with narrow LLM stages) and an evolving system maintained by a
coordinated team. The two systems are separate; future readers should not
conflate them.

## Directory tour (under `.squad/`)

- **`.squad/agents/`** — charters and history for each squad member (Holden,
  Naomi, Amos, Bobbie, Alex, Scribe, Ralph). Each agent has a `charter.md`
  (their role and responsibilities) and a `history.md` (append-only learning
  log from past spawns).
- **`.squad/decisions/`** — append-only ledger of team decisions
  (`decisions.md`) plus a working `inbox/` for new decisions pending merge
  to the main ledger.
- **`.squad/ceremonies/`** — governance rituals (planning cycles, retros,
  casting sessions, etc.).
- **`.squad/log/`** — research artifacts, brainstorms, and working notes
  from squad investigations.
- **`.squad/skills/`** — reusable patterns extracted from past work.
- **`.squad/team.md`** — roster, roles, and contact info.
- **`.squad/routing.md`** — how different types of requests route to the
  right agent.

## Standing directives

The current standing directives from `.squad/decisions.md`:

1. **docs-always-updated** — Generated docs (`docs/generated/**`) and any
   agent-derived documentation MUST stay in sync with source-of-truth files
   at all times. Every agent that touches a source file regenerates the
   corresponding generated doc in the same PR. CI enforces via the docs
   workflow and (once the safety-net workflow ships) an auto-regen job on
   `main`.

2. **SRE-as-stages-no-SRE-agent** — Skip a dedicated SRE agent in v1.
   Instead, add SRE-shaped automation as incremental deterministic stages
   (`postmortem_draft.py`, `compliance_snapshot.py`, `patch_triage.py`),
   each owned by an existing squad member. Re-evaluate if ≥6 SRE-shaped
   items accumulate.

3. **agentic-feature-roadmap** — A 10-item prioritized agentic feature
   roadmap for Phase 3, with explicit owner assignments, scoped to narrow
   LLM stages within the consensus plan. Supporting infrastructure items
   are tracked separately.

4. **squad-hidden-from-public-docs** — The `.squad/` directory and all
   squad-specific content must be hidden from the public product surface.
   Squad must appear only inside a collapsed maintainer area in README,
   with a pointer to this file for maintainers. Protects the public
   narrative (Agentic ALZ is a deterministic pipeline) from exposing
   internal coordination tooling.

## For active squad members

Maintainers actively coordinating with the squad should read:

- `.squad/team.md` — current roster and roles
- `.squad/routing.md` — how requests route to agents
- `.squad/decisions.md` — full append-only decision ledger (including the
  standing directives above)

Each squad member's `.squad/agents/<name>/charter.md` defines their role,
and `.squad/agents/<name>/history.md` tracks learnings from past spawns.
The Lead (Holden) owns AGENTS.md and sensitive-path triage; the Scribe
maintains `.squad/decisions.md` and team memory; the Coordinator (Martin)
casts agents and approves merges of decision records to the main ledger.

## Subtree convention

`docs/maintaining/` is reserved for maintainer-facing documentation that is
**not part of the product surface**. CODEOWNERS marks this subtree as
maintainer-only. End users browsing `docs/` for product information can
safely skip this directory.
