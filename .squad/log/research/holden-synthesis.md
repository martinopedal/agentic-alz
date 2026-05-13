# Holden — Agentic Feature Synthesis

**Author:** Holden (Lead / Architect / Governance)
**Date:** 2026-05-13
**Status:** Complete — pending martinopedal greenlight
**Inputs:** Naomi (orchestrator surface), Amos (pipeline/IaC/policy, 14 candidates), Bobbie (SRE/ops/security), Alex (quality gates + docs-always-updated)

---

## 1. Agentic Feature Roadmap (Top 10, Prioritized)

### Ranking Methodology

Each candidate scored on four axes:
- **Impact** — what new capability gets unlocked for the CSA or operator
- **Complexity** — S / M / L (per source agent estimate)
- **Guardrail fit** — does it sit inside the five hard guardrails, or does it require new guardrail surface?
- **Lifecycle position** — where in the bootstrap → decommission arc does it fire?

Tie-breakers: (a) unlocks other candidates, (b) lower blast radius, (c) existing scaffolding coverage.

### Top 10

| Rank | Name | Source | Owner | Lifecycle | Cmplx | Impact | Guardrail Fit | Why Here |
|------|------|--------|-------|-----------|-------|--------|---------------|----------|
| 1 | **Plan Summarizer** (WA-2 / IA-2 / IA-7) | Amos | Amos | Plan | S | Prose plan + cost commentary on every PR. Replaces manual "read 800-line plan JSON." | ✅ Fits — read-only PR comment, no mutation, no new MCP. | Cheapest win. Zero guardrail surface. Immediate CSA quality-of-life. |
| 2 | **Rubberduck Generator** (WA-5) | Amos | Alex | Plan (PR open) | M | Auto-populates `## Rubberduck` + `## Playbook` sections. Reduces rubberduck.yml failures from ~30% to ~5%. | ✅ Fits — LLM writes PR body section, human reviews before merge. | Multiplier: every PR is faster. |
| 3 | **AVM Version-Bump PRs** (IA-1) | Amos | Amos | Day-2 (weekly) | M | Automated dependency freshness. Catches AVM security patches. | ✅ Fits — PR + full CI pipeline + human merge. versions.lock + avm_pinning.rego enforce. | High security value, medium effort. |
| 4 | **Drift Triage stage** (WA-1 + existing roadmap `llm-drift-triage-stage`) | Amos+Naomi | Holden | Day-2 (nightly) | M | Classifies drift as benign / actionable. Reduces alert fatigue on CSA. | ✅ Fits — existing LLM stage slot in consensus plan. Schema-validated, never auto-merges. | Already sanctioned by consensus plan. Fills the skeleton `drift.yml`. |
| 5 | **Cost Guardrails** (IA-4) | Amos | Amos | Plan | S | Deterministic cost-policy gate. Fails plan if monthly estimate exceeds threshold. LLM explains why cost increased. | ✅ Fits — Rego/Python threshold check + advisory LLM comment. | Low complexity, high operational value. |
| 6 | **ALZ Conformance Explainer** (IA-6) | Amos | Alex | Plan (on denial) | S | Maps OPA denial → CAF/ALZ docs link. Educational: explains *why* the rule exists. | ✅ Fits — advisory PR comment, no mutation. | Cheapest quality gate. Helps onboarding CSAs. |
| 7 | **Shared PR Opener primitive** | Naomi | Naomi | Cross-cutting | M | Centralised `github/pr.py` abstraction for "open advisory PR with diff, judge attestation, rubberduck pre-fill." Prerequisite for ranks 8-10 and all M/L candidates. | ✅ Fits — internal plumbing, routes through github-mcp PR/issue surface only. | Unlocks the M-tier candidates. Without this, each stage rolls its own PR logic and we fragment rubberduck/judge enforcement. |
| 8 | **Rego Unit-Test Generation** (PA-1) | Amos | Bobbie | Plan (on policy change) | M | LLM synthesizes HCL fixtures for PASS/DENY; `opa test` verifies deterministically. | ✅ Fits — LLM proposes test code, `opa test` gates merge. | Strengthens policy surface without touching policy logic. |
| 9 | **Cost Advisor stage** | Naomi | Amos | Plan (post-plan) | S | Advisory-only cost commentary on plan output. Lighter than Cost Guardrails — no fail gate, just narration. | ✅ Fits — read-only, advisory. | Naomi flagged as cheapest new stage. Subsumable into Plan Summarizer (rank 1) or standalone. |
| 10 | **Compliance Snapshot stage** | Bobbie | Bobbie | Day-2 (monthly) | M | Read-only: query Azure Policy compliance states, RBAC audit logs → evidence bundle for auditors. | ⚠️ Needs new schema (`schemas/compliance.schema.json`) — triggers multi-model judge on schema PR. | High audit-prep value. Bobbie owns NetSec surface. |

### Honourable Mentions (11–15)

| Rank | Name | Source | Why deferred |
|------|------|--------|--------------|
| 11 | Policy Regression Detection (PA-3) | Amos | Valuable but depends on PA-1 test fixtures existing first. |
| 12 | Template Optimizer | Naomi | S complexity but narrow use case — AVM version bumps (rank 3) cover most of this. |
| 13 | Multi-Model Judge Orchestrator (WA-6) | Amos | High value but High complexity + $5-10/invocation. Keep human-driven for v1. |
| 14 | Postmortem Draft stage | Bobbie | Good fit but post-incident velocity is not v1-critical. |
| 15 | RBAC Recommender | Naomi | M complexity, requires new MCP server (microsoft-graph-mcp), NetSec gate. |

---

## 2. SRE Agent: Yes / No / How

### Decision: **Endorse Bobbie's (c) — no SRE agent for v1. Add SRE-shaped stages incrementally.**

#### Reasoning

Bobbie's analysis is thorough and aligns with the consensus plan's "narrow LLM stages" philosophy. The key arguments:

1. **Philosophy fit.** An SRE agent would own a *sprawling* surface (alerts, incidents, capacity, compliance, patching). The project's safety model depends on narrow, schema-validated I/O contracts per stage. A general-purpose SRE agent violates this.

2. **Coverage already adequate.** The two highest-value Day-2 SRE tasks — drift detection and cost reporting — are already deterministic scheduled workflows. Adding LLM triage to these (rank 4 and 5 above) is incremental, not a new agent.

3. **What we lose.** Postmortem drafting velocity (rank 14) and proactive compliance audit prep (rank 10). Both are real losses but not v1 blockers. They land as stages owned by existing squad members.

4. **What we gain by NOT adding the agent.** Simpler guardrail surface. No new "SRE agent can do X but not Y" boundary to define and police. Every SRE-shaped stage goes through the same gates as Interview/Design/Drift Triage.

#### Modification to Bobbie's recommendation

One adjustment: Bobbie recommends `stages/postmortem_draft.py` owned by Holden. I'd reassign to **Bobbie** — postmortems require security context and incident classification, which is NetSec territory. Holden reviews.

#### Future gate for re-evaluation

If the stage count reaches ≥6 SRE-shaped stages (currently projected: 3 — postmortem, compliance, patch triage), we should re-evaluate whether a Drummer agent would consolidate ownership. That's a v2 decision.

---

## 3. "Docs Always Updated" Implementation

### Decision: **Endorse Alex's two-tier pattern. No docs-steward agent.**

Alex's design is sound:

1. **Tier 1 (blocking):** `docs / generate-and-check` stays as-is. Already works. ✅
2. **Tier 2 (safety net):** New `regen-docs.yml` workflow auto-opens a PR if docs drift after a force-merge. Endorsed. ✅
3. **Tier 3 (agent inline):** Every agent regenerates docs in the same PR. Playbook DoD bullets make this explicit. ✅

#### Concrete next actions

| Action | Owner | Playbook |
|--------|-------|----------|
| Add DoD bullet to playbooks 04, 05, 06, 07: "regenerate `docs/generated/` if source changed" | Alex | `03-doc-only.md` |
| Create `.github/workflows/regen-docs.yml` per Alex's spec | Alex | `08-ci-workflow-change.md` |
| Add `evals/replay.py` and `judge.py` to AGENTS.md "never edit" list | Holden | `10-research-and-decide.md` |
| Add `coverage-gap-detection` job to `ci.yml` | Alex | `08-ci-workflow-change.md` |

#### Why no docs-steward agent

Alex is right: the pattern is one script, one commit. A dedicated agent adds a handoff, a failure mode, and a maintenance burden for zero value over the deterministic `gen_docs.py` call. Every agent can inline `python scripts/gen_docs.py && git add docs/generated/` — the skill doc (`.squad/skills/docs-always-updated/SKILL.md`) already teaches this.

---

## 4. Bootstrap → Operations Lifecycle Map

The binding constraint is AGENTS.md: "Apply is never an LLM action." The table below maps each lifecycle stage to its automation mode.

| # | Stage | Mode | Rationale |
|---|-------|------|-----------|
| 1 | **Bootstrap** | **human-only** | Identity provisioning, OIDC federation, state backend. Sensitive path (`bootstrap/`). No agent, no CI automation. |
| 2 | **Interview** | **agentic-CLI** | Local CLI only (`agentic-alz interview`). LLM stage. No CI path — CSA runs locally. Hand-edit of `inputs.yaml` is first-class. |
| 3 | **Design** | **agentic-CLI** | Local CLI only (`agentic-alz design`). LLM stage. Produces ADR + `design.json`. CSA reviews locally before pushing. |
| 4 | **Generate** | **deterministic-CI** | Template rendering from `design.json`. No LLM. Runs in `validate.yml`. |
| 5 | **Validate** | **deterministic-CI** | `fmt`, `tflint`, `checkov`, `conftest`, `terraform validate`. No LLM. Runs in `validate.yml`. |
| 6 | **Plan** | **deterministic-CI + agentic-CI** | `terraform plan` is deterministic. Plan Summarizer (rank 1) and Cost Guardrails (rank 5) are agentic enrichments — advisory comments, not gates. The plan artifact is immutable. |
| 7 | **Apply** | **deterministic-CI (protected env)** | Consumes immutable saved plan. Protected `prod` environment. Human approval. **Never agentic.** |
| 8 | **Day-2 Operate** | **agentic-CI + agentic-CLI** | Drift detection (CI, nightly), Drift Triage (LLM stage, CI), Cost reporting (CI, weekly), Cost Advisor (LLM, CI). CLI: `agentic-alz drift`, `agentic-alz cost`. All read-only. |
| 9 | **Drift Response** | **agentic-CI** | LLM classifies drift, opens issue with triage. Human decides remediation. PR is human-authored or agent-proposed but human-merged. |
| 10 | **Firewall Change** | **agentic-CLI-and-CI** | CLI: `agentic-alz firewall-compose`. CI: Composer stage opens PR to `alz-firewall-policy`. NetSec CODEOWNER merges. |
| 11 | **Incident** | **human-only** | `09-incident-response.md` playbook. LLM-assisted postmortem drafting (future stage) is post-incident, not during. |
| 12 | **Decommission** | **human-only** | `terraform destroy` is destructive. Manual + break-glass. No agent. |

**Key principle:** LLM stages live either *before* the plan artifact is frozen (Interview, Design, Rubberduck, AVM bump) or *after* apply completes (Drift Triage, Cost, Firewall Compose, Postmortem). The plan → apply gate is the deterministic core. This answers martinopedal's original question: "rely on both pipeline and CLI depending on stage" — yes, exactly as mapped above.

---

## 5. Squad Roster Recommendation

### Current roster: Holden, Naomi, Amos, Bobbie, Alex (+ Scribe, Ralph exempt)

| Candidate | Role | Verdict | Justification |
|-----------|------|---------|---------------|
| **Drummer** (SRE) | Day-2 ops, incident response, compliance | **No for v1.** | Per §2: SRE-shaped stages are owned collectively. Re-evaluate at ≥6 SRE stages. The thematic fit is also weak — Drummer is a consensus builder, not an autonomous operator. |
| **McManus** (DevRel/Docs) | Documentation authoring, onboarding, changelog | **No.** | Alex's docs-always-updated pattern + `gen_docs.py` covers the generated surface. Hand-written docs (ADRs, playbooks, guides) are authored by the domain expert, not a docs specialist. A DevRel agent would have no deterministic output to validate. |
| **MCP Tooling Specialist** | MCP server wrappers, new MCP integrations | **No.** | MCP integrations (azure-mcp, arm-mcp, terraform-mcp) are plumbing owned by Amos (infra) or Bobbie (NetSec). A specialist agent for a 6-server surface is overhead. When MCP server count reaches 10+, reconsider. |
| **Prax** (Eval/Golden-Run Curator) | Eval harness, golden run expansion, regression detection | **Maybe v1.1.** | Alex covers eval gates today, but as golden runs expand (one per prompt × topology), the curation burden grows. If `evals/golden/` exceeds 20 cases, spinning off a dedicated eval curator could help. Not urgent now. |

**Recommendation: No roster changes for v1.** The five-member squad has clean ownership boundaries and sufficient domain coverage. Revisit at v1.1 if SRE stage count or eval case count triggers the thresholds above.

---

## 6. Concrete Next Actions (5 PRs in dependency order)

| Order | PR Title | Owner | Playbook | What It Does |
|-------|----------|-------|----------|--------------|
| 1 | **feat(ci): Plan Summarizer — LLM-authored PR comment on every plan** | Amos | `01-roadmap-item.md` → `08-ci-workflow-change.md` | Adds a step to `plan.yml` that reads plan JSON + Infracost diff, calls frontier model, posts a human-readable summary as a PR comment. Advisory only, no gate. |
| 2 | **feat(ci): regen-docs.yml + playbook DoD bullets** | Alex | `08-ci-workflow-change.md` + `03-doc-only.md` | Implements Alex's two-tier docs-always-updated pattern. Adds safety-net workflow + DoD reminders to playbooks 04/05/06/07. |
| 3 | **feat(ci): Rubberduck Generator — auto-populate PR sections** | Alex | `08-ci-workflow-change.md` | Extends `rubberduck.yml` to auto-populate `## Rubberduck` and `## Playbook` from PR diff + playbook metadata. Human edits before merge. |
| 4 | **feat(orchestrator): Shared PR Opener primitive** | Naomi | `01-roadmap-item.md` | Creates `orchestrator/agentic_alz/github/pr.py` with reusable "open advisory PR with diff, judge attestation, rubberduck pre-fill" abstraction. Prerequisite for AVM bumps, drift triage PRs, etc. |
| 5 | **feat(ci): AVM Version-Bump weekly workflow** | Amos | `06-iac-template-change.md` + `08-ci-workflow-change.md` | Weekly cron queries AVM registry, compares to `versions.lock`, opens a PR with updated pins + changelog summary. Uses Shared PR Opener (PR #4). |

### ROADMAP.md changes (proposed, not applied)

The following items should be added to ROADMAP.md under `## Phase 3 — Agentic features`:

1. `plan-summarizer` — Plan Summarizer stage (agent_eligible: true, S complexity)
2. `rubberduck-generator` — Rubberduck auto-populate (agent_eligible: true, M complexity)
3. `avm-version-bump` — AVM Version-Bump weekly workflow (agent_eligible: true, M complexity)
4. `cost-guardrails` — Cost threshold gate on plan (agent_eligible: true, S complexity)
5. `alz-conformance-explainer` — OPA denial → CAF docs explainer (agent_eligible: true, S complexity)
6. `shared-pr-opener` — Shared PR opener primitive (agent_eligible: true, M complexity)
7. `rego-unit-test-gen` — LLM-assisted Rego test generation (agent_eligible: false — touches policies/, human-only)
8. `compliance-snapshot` — Compliance evidence collector (agent_eligible: false — new schema, human-only)
9. `regen-docs-workflow` — regen-docs.yml safety net (agent_eligible: true, S complexity)
10. `coverage-gap-detection` — Eval coverage gap CI job (agent_eligible: true, S complexity)

### AGENTS.md changes (proposed, not applied — requires multi-model judge)

1. Add `evals/replay.py` to "Things an agent must NEVER do" — "Never edit `evals/replay.py`."
2. Add `orchestrator/agentic_alz/llm/judge.py` to the existing "runtime enforcement points" note.
3. Both are guardrail-enforcement code that must stay deterministic.

---

## 7. Risk Register

| Risk | Mitigation |
|------|------------|
| Plan Summarizer hallucinating resource counts | Compare LLM output to deterministic plan JSON; emit warning if mismatch. |
| Rubberduck Generator masking review quality | Human must review and edit before merge; rubberduck.yml still checks for placeholders. |
| AVM Version-Bump introducing breaking changes | Full CI pipeline runs on bump PR; `avm_pinning.rego` validates. Human reviews changelog. |
| Cost Guardrails threshold too aggressive | Start with advisory-only (comment, not fail gate). Graduate to blocking after 2 weeks of data. |
| Shared PR Opener becoming a bypass vector | PR opener routes through github-mcp only; OPA enforces no `repos.create_or_update_file`. |

---

## 8. Appendix: Full Candidate Cross-Reference

| ID | Name | Source Agent | Rank | Status |
|----|------|-------------|------|--------|
| WA-2/IA-2/IA-7 | Plan Summarizer | Amos | 1 | Top 10 |
| WA-5 | Rubberduck Generator | Amos | 2 | Top 10 |
| IA-1 | AVM Version-Bump PRs | Amos | 3 | Top 10 |
| WA-1 | Drift Triage | Amos+Naomi | 4 | Top 10 (already on roadmap) |
| IA-4 | Cost Guardrails | Amos | 5 | Top 10 |
| IA-6 | ALZ Conformance Explainer | Amos | 6 | Top 10 |
| — | Shared PR Opener | Naomi | 7 | Top 10 |
| PA-1 | Rego Unit-Test Gen | Amos | 8 | Top 10 |
| — | Cost Advisor | Naomi | 9 | Top 10 (subsumable into #1) |
| — | Compliance Snapshot | Bobbie | 10 | Top 10 |
| PA-3 | Policy Regression Detection | Amos | 11 | Deferred |
| — | Template Optimizer | Naomi | 12 | Deferred |
| WA-6 | Multi-Model Judge Orchestrator | Amos | 13 | Deferred (cost) |
| — | Postmortem Draft | Bobbie | 14 | Deferred (v1.1) |
| — | RBAC Recommender | Naomi | 15 | Deferred (new MCP) |
| IA-5 | Naming/Tagging Compliance | Amos | 16 | Deferred |
| WA-7 | Cost Anomaly Alert | Amos | 17 | Deferred |
| IA-3 | Capacity Planning | Amos | 18 | Deferred (L complexity) |
| PA-2 | Policy Coverage Analysis | Amos | 19 | Deferred |
| WA-3 | Auto-Docs Companion | Amos | 20 | Superseded by docs-always-updated |
| — | Documentation Generator | Naomi | 21 | Superseded by gen_docs.py |
| — | Security Posture Review | Naomi | 22 | Deferred (L complexity) |
| — | Runbook Generator | Naomi | 23 | Deferred (L complexity) |
| — | Capacity Planner | Naomi | 24 | Deferred (L complexity) |
| PA-4 | Policy Synthesis from ADR | Amos | 25 | Low fit (Rego from prose is brittle) |
| PA-5 | OPA Bundle Freshness | Amos | 26 | Deterministic, no LLM needed |
| WA-4 | Auto-Changelog | Amos | 27 | Deterministic, no LLM needed |
| WA-8 | Bootstrap Idempotency | Amos | 28 | Low ROI, high complexity |
| — | Firewall conflicts Rego | Bobbie | — | Deterministic policy, not agentic. Add to roadmap separately. |
| — | Suspect rule scanner | Bobbie | — | Read-only, fits Day-2. Defer to post-v1. |
| — | Effective route summarizer | Bobbie | — | Needs new MCP server. Defer. |
| — | Firewall rule usage analytics | Bobbie | — | Needs Azure Monitor integration. Defer. |
| — | Patch Triage | Bobbie | — | Good fit, defer to v1.1 with postmortem. |
| — | Privileged Access Review | Bobbie | — | Good fit, subsumable into Compliance Snapshot (rank 10). |

---

**End of synthesis.**
