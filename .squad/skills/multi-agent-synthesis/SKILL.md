# SKILL: multi-agent-synthesis

**Owner:** Holden (Lead)
**Created:** 2026-05-13
**Pattern:** Synthesize multiple agent research reports into a single prioritized roadmap

---

## When to use

When 3+ squad members have produced independent research reports on overlapping domains and the Lead must produce a single coherent recommendation.

---

## Input requirements

1. Read ALL input artifacts in full before synthesizing (no partial reads).
2. Identify overlapping candidates across reports (e.g., Amos's WA-2 = Naomi's "Cost Advisor" = partial overlap).
3. Note each source agent's complexity estimate (S/M/L) and priority recommendation.

## Scoring framework

Score each candidate on four axes:

| Axis | Question |
|------|----------|
| **Impact** | What new capability gets unlocked? Who benefits? |
| **Complexity** | S (days) / M (sprint) / L (multi-sprint)? Per source estimate. |
| **Guardrail fit** | Does it sit inside the existing five hard guardrails, or does it require new guardrail surface? |
| **Lifecycle position** | Where in the bootstrap → decommission arc does it fire? |

Tie-breakers: (a) unlocks other candidates, (b) lower blast radius, (c) existing scaffolding coverage.

## Output structure

1. **Top 10 ranked table** — rank, name, source agent, owner, lifecycle, complexity, guardrail fit, justification.
2. **Honourable mentions** (11–15) with reason for deferral.
3. **Full cross-reference table** — every candidate from every report, with rank or deferral reason.
4. **Decisions on open questions** — endorse/modify/counter each pending recommendation with clear justification.
5. **Concrete next actions** — 3–5 PRs in dependency order with playbook routing.
6. **Risk register** — one row per top-5 item.

## Anti-patterns

- **Don't merge overlapping candidates silently.** Call out the merge (e.g., "WA-2 + IA-2 + IA-7 are the same feature from different angles → merged as Plan Summarizer").
- **Don't rank by source agent loyalty.** Rank by impact × feasibility.
- **Don't defer everything to v2.** The user asked for actionable now.
- **Don't propose changes that violate AGENTS.md.** If a candidate requires new guardrail surface, flag it explicitly.

---

**End of skill doc.**
