# Scribe — History

**Project:** Agentic ALZ — deterministic GitOps pipeline for Azure Landing Zones.
**Repo:** martinopedal/agentic-alz
**Cast at:** 2026-05-12T22:36:05Z

## Core Context

- Append-only files (decisions.md, history.md, log/, orchestration-log/) merge with the `union` driver per `.gitattributes`.
- `decisions.md` archive threshold: ~20 KB → archive entries older than 30 days to `decisions-archive.md`.
- `history.md` summarization threshold: ~12 KB.

## Learnings

### 2026-05-13: Inbox-to-ledger merge + session/orchestration logging workflow

**Cycle:** greenlight-top5 + squad-hidden-from-public-docs

**Key patterns established:**

- **Inbox-archive flow:** After each spawn batch, Scribe merges inbox files to decisions.md (append-only, H2 entries, preserving existing format), then archives the source files to `.squad/decisions/archive/{YYYY-MM-DD}/`. This maintains auditability (archived sources link from ledger entries) while keeping decisions.md as the single source of truth. Archive threshold: decisions.md grows; when ~20 KB, consider rotating to decisions-archive.md.

- **Session log vs. orchestration log distinction:** Session log is *agent-centric* — full turn-by-turn outcomes, learnings extracted by each agent, key incidents (line-ending gotcha, docs drift discovery), next actions for the human. Orchestration log is *coordinator-centric* — what decisions were made, which agents ran, files changed, PRs opened. Session log is for understanding the *work*, orchestration log is for understanding *who did what*.

- **Decision entry structure preservation:** Each merged decision should include: status, requested_by, decided_at (today), summary (1–3 sentences), links to source files + PRs, and alternatives_considered (where applicable). The existing 4 standing directives in decisions.md set the precedent; follow their depth and cross-reference patterns.

- **Naming collisions require explicit disambiguation:** When Martin surfaced the visibility question mid-cycle, his new directive (squad-hidden-from-public-docs) named a genuine collision: "squad" means two things in this repo (public GitHub-issue automation via scripts/squad_bootstrap.py, and internal coordination tooling under `.squad/`). The ledger entry captured his verbatim directive + enumeration of all 4 options + choice rationale. Future PRs that touch README or public docs should check this entry to avoid re-surfacing the issue.

- **Re-ranking signals urgent re-evaluation:** When Holden discovered that gen_docs.py drift was breaking a standing directive, regen-docs-backstop was instantly promoted from supporting-infra to rank #1. The ledger entry captured this with a note: "Supporting infrastructure can become urgent when new evidence surfaces." This pattern should be referenced if any future item needs priority re-evaluation.

**Applied in:** 3 decisions merged to decisions.md; 3 inbox files archived; session + orchestration logs written; this history entry appended.

(append below — newest at top)
