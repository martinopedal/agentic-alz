# `.squad/` — local coordination layer (maintainer guide)

> **Audience.** Repo maintainers (currently `@martinopedal`). This page
> documents the [`.squad/`](../.squad/) directory itself: what it is,
> why it is committed in the open, and the conventions every entry must
> follow. The cloud-agent (GitHub-side) bootstrapper is a different
> system — see [`docs/squad.md`](squad.md) for that.

## Why `.squad/` is committed (not `.gitignore`d)

`agentic-alz` is itself an experiment in *agentic GitOps* — a deterministic
pipeline with narrow LLM stages, multi-model judges, OPA gates, and an
auditable trail back to the human who pressed go. The `.squad/`
directory is the same evidence pattern applied to the development of
this repo: each multi-agent session leaves an append-only ledger of what
was decided, an agent-history file of what each persona did, and a
research log behind every synthesis. Hiding that trail would contradict
the very property we are trying to demonstrate, so we keep it visible
and gate it with [`CODEOWNERS`](../CODEOWNERS) instead.

This is consistent with the
[`hide-internal-tooling-behind-maintainer-area`](../.squad/skills/hide-internal-tooling-behind-maintainer-area/SKILL.md)
skill's reversal entry in [`decisions.md`](../.squad/decisions.md):
"the squad layer is *part of the agentic showcase*, not a private
implementation detail".

## Layout

| Path | Purpose | Edit policy |
| --- | --- | --- |
| [`.squad/team.md`](../.squad/team.md) | Roster of personas and their areas | Hand-edit |
| [`.squad/routing.md`](../.squad/routing.md) | Which persona owns which task | Hand-edit |
| [`.squad/ceremonies.md`](../.squad/ceremonies.md) | Standing meetings (synthesis, retros) | Hand-edit |
| [`.squad/agents/<name>/charter.md`](../.squad/agents/) | One-line description + scope per persona | Hand-edit |
| [`.squad/agents/<name>/history.md`](../.squad/agents/) | Append-only per-agent activity log | **Append-only** (`merge=union`) |
| [`.squad/decisions.md`](../.squad/decisions.md) | Canonical append-only decision ledger; H3 entries `### {ISO timestamp}: {title}` | **Append-only** (`merge=union`) |
| [`.squad/decisions/inbox/`](../.squad/decisions/inbox/) | Drop zone for decision drafts before they are folded into `decisions.md` | Hand-edit |
| [`.squad/decisions/archive/<date>/`](../.squad/decisions/archive/) | Long-form per-decision records once superseded or archived | Hand-edit (rarely) |
| [`.squad/log/sessions/<date>-<name>.md`](../.squad/log/sessions/) | Per-session human-readable narrative | Append-only |
| [`.squad/log/orchestration/<date>-<name>.md`](../.squad/log/orchestration/) | Multi-agent dispatch trail per session | Append-only |
| [`.squad/log/research/<persona>-<topic>.md`](../.squad/log/research/) | Long-form research artefacts behind syntheses | Hand-edit |
| [`.squad/orchestration-log/`](../.squad/orchestration-log/) | Legacy 2026-05-12 init logs (kept for provenance) | Frozen |
| [`.squad/casting/`](../.squad/casting/) | Persona casting registry, policy, history (machine-readable) | Generated |
| [`.squad/skills/<name>/SKILL.md`](../.squad/skills/) | Reusable, named workflow snippets the squad invokes by handle | Hand-edit |

The append-only files use `merge=union` via
[`.gitattributes`](../.gitattributes) so two parallel agents appending
entries do not produce a conflict.

## Conventions

1. **Decision ledger entries** are H3 headers of the form
   `### {ISO-8601 UTC timestamp}: {short title}` followed by a short
   paragraph and (for reversals) a `Supersedes:` line listing the
   `### …` headers being marked obsolete. Old entries are **never
   deleted** — supersession is the reversal mechanism (see
   [`reversal-without-rewriting-history`](../.squad/skills/) skill if
   present, otherwise the example reversal at
   `2026-05-13T15:00:00Z` in [`decisions.md`](../.squad/decisions.md)).
2. **Agent histories** are H3 entries of the form
   `### {ISO timestamp}: {short verb-phrase}` referencing the session
   log path, the issue/PR numbers touched, and the decisions citation.
3. **Session logs** open with a frontmatter block (`session-id`,
   `date`, `participants`, `outcome`) and close with a "Next steps"
   list that is mirrored as roadmap items where appropriate.
4. **Research logs** must end in a `## References` section with at
   least three live URLs (link-checked weekly).

## Spawning a session

The lightweight Ralph pattern — "open a fresh agent, give it the open
issues that are ready, let it work, fold its summary into history" — is
documented in `.squad/team.md` under the Ralph charter. The
orchestration trail of any such session lives at
`.squad/log/orchestration/<date>-<name>.md` and the human-readable
narrative at `.squad/log/sessions/<date>-<name>.md`. Start the file
with the same frontmatter as previous sessions; close it with a Next
Steps list and a Decisions list that have been folded into
[`decisions.md`](../.squad/decisions.md).

## Promotion paths

| From | Becomes | When |
| --- | --- | --- |
| Decision ledger entry | `ROADMAP.md` item with `agent_eligible: true/false` | Decision implies a build task |
| Decision ledger entry | New playbook under `docs/playbooks/` | Decision changes how a sensitive surface is touched |
| Research log | `decisions/archive/<date>/<topic>.md` (long form) | Synthesis is durable enough to cite |
| Skill | `docs/playbooks/` (for repo-public skills) | Skill is sanctioned for general use |

## Boundary with other surfaces

- `.squad/` **never** mutates Azure or the `apply.yml` workflow. It is
  a *coordination* layer over the same five hard guardrails in
  [`AGENTS.md`](../AGENTS.md).
- `.squad/` **never** edits files owned by other CODEOWNERS without
  going through a normal PR — the ledger reflects the decision; the PR
  reflects the change.
- The cloud-agent (GitHub-side) board described in
  [`docs/squad.md`](squad.md) is upstream of `.squad/` — decisions
  taken in `.squad/decisions.md` typically promote to roadmap entries
  that the cloud-agent picks up via `scripts/squad_bootstrap.py`.

## Kill switch

The `AGENTIC_ALZ_DISABLED` repo variable / env var (per MUST #1 in
[`AGENTS.md`](../AGENTS.md)) gates **every** mutation in this repo,
including squad-driven ones. When it is on, the appropriate squad
response is to *append a ledger entry recording why state-mutating work
was paused* and stop, not to find a workaround.

## References

- [`AGENTS.md`](../AGENTS.md) — repo-wide agent instructions and the
  five hard guardrails this layer respects.
- [`docs/squad.md`](squad.md) — the cloud-agent (GitHub-side)
  bootstrapper. Adjacent system, different purpose.
- [`docs/copilot-developer-setup.md`](copilot-developer-setup.md) —
  which Copilot CLI / VS Code features are sanctioned for this repo.
- [`docs/local-dev.md`](local-dev.md) — running every CI gate on a
  developer laptop.
- [`.squad/team.md`](../.squad/team.md) — current persona roster.
- [`.squad/decisions.md`](../.squad/decisions.md) — canonical
  append-only ledger.
- [`.gitattributes`](../.gitattributes) — `merge=union` rules that
  make the append-only files safe under parallel writers.
