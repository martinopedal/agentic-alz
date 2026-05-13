# Amos — History

**Project:** Agentic ALZ — deterministic GitOps pipeline for Azure Landing Zones (ALZ Accelerator + AVM + Terraform), with narrow LLM stages (Interview, Design, Drift Triage, Firewall Composer). Apply is never an LLM action.
**Stack:** Python 3 (orchestrator), Terraform/AVM (templates), OPA Rego (policies), GitHub Actions, MCP, frontier LLMs
**Repo:** martinopedal/agentic-alz
**Lead user:** martinopedal
**Cast at:** 2026-05-12T22:36:05Z

## Core Context

- AVM pinning: every module in `templates/**` MUST be `Azure/avm-{res,ptn}-*/azurerm` at exact semver, listed in matching `versions.lock`. Enforced by `policies/avm_pinning.rego`.
- OPA validation: `conftest test --parser hcl2 --policy policies --namespace alz.avm_pinning templates/hub-and-spoke/*.tf`.
- Apply path is human-only: `.github/workflows/apply.yml` and the protected `prod` env mutate Azure. Plan path: `plan.yml` + SHA-256 content-addressed tfplan.
- Bootstrap (`bootstrap/`) is phase-1 identity provisioning. Human-authored PRs only.
- Workflows of note: `ci.yml`, `apply.yml`, `plan.yml`, `docs.yml`, `rubberduck.yml`, `copilot-setup-steps.yml`, `squad.yml`.

## Learnings

(append below — newest at top)

### 2026-05-13: Roadmap assignments — Phase 3 agentic features

**Assigned items (priority rank):**
1. Plan Summarizer (rank 1) - Plan stage, advisory LLM prose on plan PRs
3. AVM Version-Bump (rank 3) - Day-2, weekly cron opens version-bump PRs
5. Cost Guardrails (rank 5) - Plan stage, threshold-based policy gates
9. Cost Advisor (rank 9) - Plan stage, cost anomaly detection + advisory

**Implementation order:** Plan Summarizer (immediate, high impact), AVM Version-Bump (toil reduction), Cost Guardrails (risk mitigation), Cost Advisor (enrich plan advisory).

**Pattern to establish:** All 4 items follow same playbook (06-iac-template-change or new agentic-feature playbook). Each must pre-fill rubberduck, honor frontier-model allowlist, schema validation, kill-switch. Shared PR Opener (Naomi, rank 7) is the critical enabler.

**Interdependency:** Cost Advisor depends on Infracost + cost_threshold_monthly variable. Guardrails and Advisor can be concurrent. Plan Summarizer is independent and should ship first to establish the pattern.

### 2025-01-26: Pipeline Surface Research — 14 Automation Candidates Identified

**Charter:** Inventory current pipeline (11 workflows, 5 OPA policies, Terraform templates, bootstrap scripts) + propose agentic automation candidates within deterministic GitOps model.

**Findings:**
- **Pipeline map**: 11 workflows split into core apply path (validate→plan→apply) + 8 supporting workflows (ci, docs, eval, drift, cost, rubberduck, copilot-setup, squad).
- **Apply constraint**: `apply.yml` consumes immutable SHA-256 content-addressed tfplan from `plan.yml`. Never re-plans. Protected `prod` environment gate. This is non-negotiable.
- **Agentic boundaries**: LLM automation fits **before** plan freeze (Interview, Design, Rubberduck generation, AVM version bumps) or **after** apply (Drift triage, Cost anomaly detection, Firewall composition). Never IN the apply path.
- **Policy surface**: 5 Rego files (avm_pinning, mcp_allowlist, firewall_rules, naming, alz_conformance). All deterministic enforcement. **PA-1** (unit-test generation) and **PA-3** (regression detection) are high-value automation candidates.
- **IaC surface**: AVM-pinned templates in `templates/hub-and-spoke/` with versions.lock. **IA-1** (AVM version-bump PRs), **IA-2** (template diff summarizer), **IA-4** (cost guardrails), **IA-5** (naming/tagging compliance), **IA-6** (ALZ conformance explainer) fit existing playbooks (05, 06).
- **Workflow surface**: **WA-1** (drift triage), **WA-2** (plan summarizer), **WA-5** (rubberduck generator), **WA-6** (multi-model judge orchestrator) enhance human decision-making without bypassing review gates.
- **8-stage lifecycle**: Bootstrap → Interview (LLM) → Design (LLM) → Plan (deterministic) → Apply (human-only) → Day-2 (LLM triage) → Drift Response (LLM triage) → Firewall Change (LLM compose) → Decommission (human-only). The plan/apply gate (stages 4-5) is the deterministic core.
- **Top 3 priorities**: WA-2 (plan summarizer — immediate impact, low complexity), IA-1 (AVM version-bump PRs — reduces toil), WA-5 (rubberduck generator — reduces PR failures).

**Output:** `.squad/log/research/amos-pipeline-surface.md` — 6-section report with consolidated table of 14 candidates ranked by impact × feasibility.

**Key learning:** Rego is deterministic *enforcement*, not synthesis. LLM can generate Rego *unit tests* (PA-1), but not runtime policy synthesis. The agentic surface is pre-plan or post-apply, never in the apply path.
