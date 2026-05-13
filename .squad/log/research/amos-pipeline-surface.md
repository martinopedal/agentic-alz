# Agentic ALZ Pipeline Surface — Research Report

**Persona:** Amos, the Platform Engineer  
**Charter:** Inventory the current pipeline surface (11 GitHub workflows, 5 OPA policies, Terraform templates, bootstrap scripts) and propose agentic automation candidates within the deterministic GitOps model. Focus on pipeline/IaC/policy automation that respects the hard constraint: **Apply is never an LLM action.**

**Date:** 2025-01-26  
**Status:** ✅ Complete

---

## Section 1: Current Pipeline Map (11 workflows)

### Core Apply Path (3 workflows: validate → plan → apply)

| Workflow | Trigger | Deterministic Stages | LLM Stage | Mutation Surface | Apply Gate |
|----------|---------|----------------------|-----------|------------------|------------|
| **validate.yml** | `workflow_call` | killswitch → Azure OIDC → `terraform fmt -check` → `tflint` → `checkov` → `conftest` (AVM pinning + naming) → `terraform validate -backend=false` | None | Read-only | N/A |
| **plan.yml** | `workflow_call` | killswitch → Azure OIDC → `terraform plan -out=tfplan` → SHA-256 hash → upload artifact → Infracost diff → risk classification (low/medium/high) | None | Read-only | Produces immutable artifact |
| **apply.yml** | `workflow_call` | killswitch → Azure OIDC → download saved plan → verify freshness (<24h) → tf-policy check → `terraform apply tfplan` → post-apply drift check | None | **Mutates Azure** | Protected `prod` environment gate |

**Key Insight:** The plan artifact is content-addressed (SHA-256) and must be <24h old. Apply never re-plans. This is the deterministic GitOps guarantee.

---

### Supporting Workflows (8 workflows)

| Workflow | Trigger | Purpose | Deterministic Stages | LLM Opportunity |
|----------|---------|---------|----------------------|-----------------|
| **ci.yml** | PR/push to main | Continuous integration gate | killswitch → Python lint/test → schema validation → OPA unit tests → lint-instructions check → gen_docs check | None (all deterministic) |
| **docs.yml** | PR on sensitive paths (`prompts/**`, `schemas/**`, `docs/models.allowlist.yaml`, `docs/mcp.allowlist.yaml`) | Enforce `scripts/gen_docs.py` freshness | killswitch → verify allowlists parse → regenerate docs/generated/ → fail if diff | None (deterministic) |
| **eval.yml** | PR + manual dispatch | Replay golden runs through offline stages | killswitch → run `evals/replay.py` (offline, no LLM calls) | None (offline validation) |
| **drift.yml** | Nightly cron + manual | Detect unmanaged changes in Azure | killswitch → (skeleton: would run `plan -detailed-exitcode` + cooldown check + open issue) | **Post-apply LLM stage**: Drift triage (classify drift as benign vs actionable) |
| **cost.yml** | Weekly cron | Track cost trends | killswitch → (skeleton: would run `infracost breakdown` + open/update issue) | **Post-apply LLM stage**: Cost anomaly detection (flag unexpected spend spikes) |
| **rubberduck.yml** | PR events | Enforce PR template completeness | killswitch (soft-fail) → check PR body for `## Playbook`, `## Rubberduck`, `## Multi-model judge`, `## Frontier-model attestation` sections → fail if placeholders remain | None (deterministic template enforcement) |
| **copilot-setup-steps.yml** | Copilot cloud agent init | Pre-warm agent environment | Install Python 3.11 + orchestrator[dev] + Terraform 1.9.8 + Conftest 0.56.0 | None (toolchain provisioning) |
| **squad.yml** | PR/push/daily cron | Auto-assign roadmap items to @copilot | killswitch → dry-run on PR (surface plan) / bootstrap on push (upsert GitHub issues from ROADMAP.md, assign @copilot if `agent_eligible: true`) | **Pre-planning LLM stage**: Roadmap item expansion (break epics into granular tasks) |

**Key Insight:** Drift and cost workflows are skeletons awaiting LLM triage stages. These are **post-apply** (read-only) surfaces where agentic automation fits naturally.

---

## Section 2: Policy Automation Candidates (5 OPA policies)

### Current Rego Enforcement (policies/)

| Policy File | Enforces | Runtime | Cross-checks |
|-------------|----------|---------|--------------|
| **avm_pinning.rego** | MUST #4: AVM modules only, exact semver, membership in versions.lock | `conftest test --parser hcl2 --policy policies --namespace alz.avm_pinning templates/**/*.tf` | `data.versions_lock` (parsed from templates/hub-and-spoke/versions.lock) |
| **mcp_allowlist.rego** | MUST #3: MCP server allowlist with NetSec gate for write mode | `conftest test --data docs/mcp.allowlist.yaml --policy policies --namespace alz.mcp_allowlist` | Requires `netsec_approval` block for `mode: write`; forbids github-mcp from push/workflow/environment tools |
| **firewall_rules.rego** | Firewall hygiene: no wildcard destinations/ports/protocols, no overly broad FQDN wildcards | `conftest test --parser json --policy policies --namespace alz.firewall_rules firewall-policy/**/*.json` | None (standalone rule surface) |
| **naming.rego** | Lower-case kebab 3-63 chars on named resource kinds (RG, VNet, Firewall, etc.) | `conftest test --parser hcl2 --policy policies --namespace alz.naming templates/**/*.tf` | None (standalone naming convention) |
| **alz_conformance.rego** | ALZ architecture guardrails: no public IPs on mgmt subnet, no Owner roles outside mgmt groups, diag settings required on hub resources, allowed regions only | `conftest test --parser hcl2 --policy policies --namespace alz.alz_conformance templates/**/*.tf` | None (standalone ALZ pattern enforcement) |

---

### Automation Candidates (Policy Surface)

| Candidate | Trigger | Input | Output | Enforcement Point | Playbook | Complexity | Agentic Fit |
|-----------|---------|-------|--------|-------------------|----------|------------|-------------|
| **PA-1: Rego Unit-Test Generation** | On policy change (PR touching `policies/**`) | Policy file + docstring | `policies/<name>_test.rego` with pass/fail cases | `ci.yml` → `opa test policies/ -v` | `05-policy-change.md` | Medium | **High** — LLM can synthesize HCL fixtures that should PASS vs DENY. Deterministic verification via `opa test`. |
| **PA-2: Coverage Analysis** | On policy change (PR touching `policies/**`) | Policy file + test file | Coverage report (% of rules exercised) | `ci.yml` → `opa test --coverage policies/` | `05-policy-change.md` | Low | **Medium** — Useful for PR review, but coverage % is computed deterministically. LLM can suggest additional test cases to hit uncovered branches. |
| **PA-3: Regression Detection** | On template change (PR touching `templates/**`) | Old policy results vs new policy results on golden fixtures | Diff report: new denials, resolved denials | `ci.yml` → compare `conftest` output before/after | `06-iac-template-change.md` | Medium | **High** — LLM can classify regressions as breaking vs expected. Feeds into PR review. |
| **PA-4: Policy Synthesis from ADR** | On ADR approval (new file in `docs/adr/` with status: accepted) | ADR text + schemas/constraints.yaml | Draft `policies/<name>.rego` + `policies/<name>_test.rego` | Human review → PR → `ci.yml` | `10-research-and-decide.md` → `05-policy-change.md` | High | **Low** — Rego synthesis from prose is brittle. Better to auto-generate *test cases* from ADR acceptance criteria, then human writes Rego. |
| **PA-5: Bundle Freshness Check** | Weekly cron | OPA version in copilot-setup-steps.yml vs latest stable | Issue if >1 minor version behind | `ci.yml` or new workflow | None (new automation) | Low | **Low** — Deterministic version check. No LLM needed. |

**Recommendation:** Prioritize **PA-1** (unit-test generation) and **PA-3** (regression detection). Both are high-value, deterministic verification, and fit the 05/06 playbooks.

---

## Section 3: IaC Automation Candidates (Terraform templates)

### Current Template Structure (templates/hub-and-spoke/)

- **main.tf**: Golden ALZ pattern (hub-and-spoke + Azure Firewall Premium), 9 AVM modules pinned to exact semver
- **versions.tf**: Terraform 1.9.8+, Azure provider >=4.15
- **variables.tf**: Input schema (location, address_spaces, tags, firewall_policy_id, etc.)
- **outputs.tf**: Exported resource IDs (hub_vnet_id, firewall_public_ip, log_analytics_workspace_id, etc.)
- **versions.lock**: JSON allowlist of 9 approved AVM modules cross-checked by avm_pinning.rego

---

### Automation Candidates (IaC Surface)

| Candidate | Trigger | Input | Output | Enforcement Point | Playbook | Complexity | Agentic Fit |
|-----------|---------|-------|--------|-------------------|----------|------------|-------------|
| **IA-1: AVM Version-Bump PRs** | Weekly cron | Current versions.lock + AVM registry | PR with updated versions.lock + templates/*.tf | `ci.yml` → policy checks → human review | `06-iac-template-change.md` | Medium | **High** — LLM can summarize AVM changelog, flag breaking changes, update versions.lock + module blocks. Human reviews & merges. |
| **IA-2: Template Diff Summarizer** | On template change (PR touching `templates/**`) | Git diff + plan output | PR comment with human-readable summary | `plan.yml` → post result to PR | `06-iac-template-change.md` | Low | **High** — LLM translates Terraform diff + plan into prose. Already fits deterministic pipeline (plan → summarize → human review → apply). |
| **IA-3: Capacity Planning Assistant** | On plan (workflow_call) | Plan output + current Azure quota | Warning if plan will exceed quota | `plan.yml` → query Azure API → compare | `06-iac-template-change.md` | High | **Medium** — Requires Azure API integration. Useful for large-scale deployments, but adds complexity. |
| **IA-4: Cost Guardrails** | On plan (workflow_call) | Infracost diff output + cost policy | Fail if estimated monthly cost exceeds threshold | `plan.yml` → Infracost → policy check | `06-iac-template-change.md` | Low | **High** — Deterministic cost policy enforcement. Can be Rego or Python script. LLM can explain *why* cost increased (e.g., "Firewall Premium tier adds $X/month"). |
| **IA-5: Naming/Tagging Compliance** | On template change (PR touching `templates/**`) | Templates + naming/tagging policy | Auto-fix PR or comment with suggested renames | `ci.yml` → naming.rego → suggest fixes | `06-iac-template-change.md` | Low | **High** — LLM can auto-fix variable names, resource names, tags to comply with naming.rego. Falls back to comment if ambiguous. |
| **IA-6: ALZ Conformance Explainer** | On policy denial (alz_conformance.rego) | Denial message + template context | PR comment explaining *why* the rule exists + link to ALZ docs | `ci.yml` → post explainer | `06-iac-template-change.md` | Low | **High** — Educational feedback loop. LLM maps denial to CAF/ALZ docs (e.g., "Public IPs are denied on management subnet per ALZ security baseline — see [link]"). |
| **IA-7: Plan Summarizer (Human-Readable)** | On plan (workflow_call) | JSON plan output | Markdown summary: resources added/changed/destroyed, risk classification | `plan.yml` → generate summary → artifact | `06-iac-template-change.md` | Low | **High** — Already implicit in plan.yml (risk classification). LLM can enrich with prose summary. |
| **IA-8: Migration Assistance (AVM 1.x → 2.x)** | On AVM major version bump | Old module version + new module version + AVM changelog | Migration guide + updated templates | Human-triggered | `06-iac-template-change.md` | High | **Medium** — High value for major version bumps, but requires deep AVM knowledge. Better as human-in-the-loop tool. |

**Recommendation:** Prioritize **IA-1** (AVM version-bump PRs), **IA-2** (template diff summarizer), **IA-4** (cost guardrails), **IA-5** (naming/tagging compliance), **IA-6** (ALZ conformance explainer). All fit the deterministic pipeline and enhance human decision-making without bypassing review.

---

## Section 4: GitHub Actions Automation (Workflow Surface)

### Automation Candidates (Workflow Surface)

| Candidate | Trigger | Input | Output | Enforcement Point | Playbook | Complexity | Agentic Fit |
|-----------|---------|-------|--------|-------------------|----------|------------|-------------|
| **WA-1: Scheduled Drift-Detection PRs** | Nightly cron (drift.yml) | Plan diff (detailed-exitcode=2) + last apply SHA | PR with drift summary + triage (benign vs actionable) | `drift.yml` → open PR → human review | `02-bug-fix.md` or new playbook | Medium | **High** — LLM triages drift (e.g., "Azure added default NSG rule — benign" vs "Firewall rule deleted — actionable"). Fits post-apply read-only surface. |
| **WA-2: PR-Comment Plan Summarizer** | On plan (workflow_call) | Plan JSON + Infracost diff | PR comment with human-readable summary + cost impact | `plan.yml` → post comment | `06-iac-template-change.md` | Low | **High** — Same as IA-2 but at workflow level. LLM enriches plan output for human reviewers. |
| **WA-3: Auto-Docs Companion** | On PR (touching code) | PR diff | PR comment suggesting doc updates | `ci.yml` → check if docs/ needs update | `03-doc-only.md` | Low | **Medium** — Useful for catching stale docs, but prone to false positives. Better as opt-in check. |
| **WA-4: Auto-Changelog** | On merge to main | PR title + body + labels | Update CHANGELOG.md | `ci.yml` → commit to main | None (new automation) | Low | **Low** — Deterministic (no LLM needed). Use Keep a Changelog format + conventional commits. |
| **WA-5: Rubberduck Generator** | On PR open (rubberduck.yml) | PR diff + playbook metadata | Auto-populate `## Rubberduck` and `## Playbook` sections | `rubberduck.yml` → update PR body | `05-policy-change.md`, `06-iac-template-change.md` | Medium | **High** — LLM maps PR to playbook, generates rubberduck summary. Human reviews & edits before merge. Reduces rubberduck.yml failures. |
| **WA-6: Multi-Model Judge Orchestrator** | On PR (touching sensitive paths) | PR diff + frontier-model responses | Populate `## Multi-model judge` section with unanimous PASS/FAIL | `docs.yml` → run judge → update PR | `04-prompt-or-schema-change.md` | High | **High** — Already required by MUST #2. Can be automated (call 2+ frontier models, compare outputs, populate PR section). Human reviews judge output. |
| **WA-7: Cost Anomaly Alert** | Weekly cron (cost.yml) | Infracost trend data + last 4 weeks baseline | Issue if current cost >20% vs baseline | `cost.yml` → open issue | None (new automation) | Low | **Medium** — LLM can explain *why* cost increased (e.g., "Firewall Premium tier added in PR #42"). Deterministic threshold check + LLM narration. |
| **WA-8: Bootstrap Idempotency Validator** | On bootstrap change (PR touching `bootstrap/**`) | bootstrap/phase1.sh + test Azure subscription | Dry-run report: resources that would be created/updated | New workflow or ci.yml | `08-ci-workflow-change.md` | High | **Low** — Requires test Azure sub. High complexity, low ROI (bootstrap is infrequent + sensitive). |

**Recommendation:** Prioritize **WA-1** (drift triage), **WA-2** (plan summarizer), **WA-5** (rubberduck generator), **WA-6** (multi-model judge orchestrator). All enhance human decision-making without bypassing the deterministic pipeline.

---

## Section 5: Bootstrap-to-Operations Lifecycle (8 stages)

| Stage | Trigger | CI Path | Local CLI Path | Agentic Stage Placement | LLM Opportunity |
|-------|---------|---------|----------------|------------------------|-----------------|
| **1. Bootstrap** | One-time (new Azure tenant) | N/A (human-run script) | `bash bootstrap/phase1.sh` | None | **Low** — Identity provisioning is sensitive. Keep human-run. |
| **2. Interview** | CSA starts engagement | N/A (local-only) | `agentic-alz interview` | **LLM stage**: Prompt user for inputs, emit inputs.yaml | **High** — Already designed as LLM stage. Fits consensus-plan.md. |
| **3. Design** | After interview | N/A (local-only) | `agentic-alz design inputs.yaml` | **LLM stage**: Synthesize ADR + design.json from inputs | **High** — Already designed as LLM stage. Fits consensus-plan.md. |
| **4. Plan** | After design | `plan.yml` (workflow_call) | `terraform plan` | None (deterministic) | **Low** — Terraform plan is deterministic. Can add *summarizer* post-plan. |
| **5. Apply** | After plan approval | `apply.yml` (protected env) | N/A (blocked) | None (deterministic) | **None** — Apply is never an LLM action (hard constraint). |
| **6. Day-2 Operations** | Post-apply | N/A (local + CI) | `agentic-alz drift` / `agentic-alz cost` | **LLM stage**: Drift triage, cost anomaly detection | **High** — Read-only post-apply surface. Fits WA-1, WA-7. |
| **7. Drift Response** | Drift detected | `drift.yml` → PR | Human reviews PR | **LLM stage**: Classify drift, suggest fix (terraform import vs manual revert) | **High** — LLM triages, human decides. Fits WA-1. |
| **8. Firewall Change** | Firewall rule request | N/A (local-only) | `agentic-alz firewall-compose request.yaml` | **LLM stage**: Generate PR to firewall-policy/ lib | **High** — Already designed as LLM stage. Fits consensus-plan.md + 07-firewall-lib-exemplar.md. |
| **9. Decommission** | Tenant shutdown | N/A (human-run script) | `terraform destroy` (manual) | None | **Low** — Destructive action. Keep human-run. |

**Key Insight:** The 8-stage lifecycle has 4 natural LLM surfaces: Interview (stage 2), Design (stage 3), Day-2 Operations (stage 6), Drift Response (stage 7), Firewall Change (stage 8). All are **before** the plan artifact is frozen or **after** apply completes. The plan/apply gate (stages 4-5) remains deterministic.

---

## Section 6: Consolidated Automation Candidates (Ranked by Impact × Feasibility)

| Rank | ID | Name | Trigger | Input | Output | Enforcement | Playbook | Complexity | Agentic Fit | Priority |
|------|----|------|---------|-------|--------|-------------|----------|------------|-------------|----------|
| 1 | **WA-2** | Plan Summarizer | On plan (workflow_call) | Plan JSON + Infracost diff | PR comment with prose summary + cost impact | `plan.yml` → post comment | 06 | Low | High | **P0** |
| 2 | **IA-1** | AVM Version-Bump PRs | Weekly cron | versions.lock + AVM registry | PR with updated versions + changelog summary | `ci.yml` → policy checks | 06 | Medium | High | **P0** |
| 3 | **WA-5** | Rubberduck Generator | On PR open | PR diff + playbook metadata | Auto-populate `## Rubberduck` and `## Playbook` sections | `rubberduck.yml` → update PR | 05, 06 | Medium | High | **P0** |
| 4 | **WA-1** | Drift Triage | Nightly cron (drift.yml) | Plan diff + last apply SHA | PR with drift summary + triage (benign vs actionable) | `drift.yml` → open PR | 02 or new | Medium | High | **P1** |
| 5 | **IA-4** | Cost Guardrails | On plan (workflow_call) | Infracost diff + cost policy | Fail if cost exceeds threshold + LLM explanation | `plan.yml` → policy check | 06 | Low | High | **P1** |
| 6 | **IA-6** | ALZ Conformance Explainer | On policy denial | Denial message + template context | PR comment explaining rule + link to CAF docs | `ci.yml` → post explainer | 06 | Low | High | **P1** |
| 7 | **WA-6** | Multi-Model Judge Orchestrator | On PR (sensitive paths) | PR diff + frontier-model responses | Populate `## Multi-model judge` section | `docs.yml` → run judge | 04 | High | High | **P1** |
| 8 | **PA-1** | Rego Unit-Test Generation | On policy change | Policy file + docstring | `policies/<name>_test.rego` with pass/fail cases | `ci.yml` → opa test | 05 | Medium | High | **P2** |
| 9 | **IA-5** | Naming/Tagging Compliance | On template change | Templates + naming.rego | Auto-fix PR or comment with suggested renames | `ci.yml` → suggest fixes | 06 | Low | High | **P2** |
| 10 | **PA-3** | Policy Regression Detection | On template change | Old vs new policy results | Diff report: new denials, resolved denials | `ci.yml` → compare conftest | 06 | Medium | High | **P2** |
| 11 | **WA-7** | Cost Anomaly Alert | Weekly cron (cost.yml) | Infracost trend + baseline | Issue if cost >20% vs baseline + LLM explanation | `cost.yml` → open issue | None | Low | Medium | **P3** |
| 12 | **IA-3** | Capacity Planning Assistant | On plan | Plan output + Azure quota | Warning if plan exceeds quota | `plan.yml` → query Azure API | 06 | High | Medium | **P3** |
| 13 | **WA-3** | Auto-Docs Companion | On PR | PR diff | PR comment suggesting doc updates | `ci.yml` → check docs/ | 03 | Low | Medium | **P3** |
| 14 | **PA-2** | Coverage Analysis | On policy change | Policy + test file | Coverage report + suggestions | `ci.yml` → opa test --coverage | 05 | Low | Medium | **P3** |

**P0 = Immediate impact, fits existing workflows, low complexity**  
**P1 = High value, requires moderate integration**  
**P2 = Enhances quality, secondary to P0/P1**  
**P3 = Nice-to-have, deferred until P0/P1/P2 complete**

---

## Executive Summary

Agentic ALZ's deterministic GitOps model (immutable plan artifact → protected-env apply) creates natural boundaries for LLM automation: **before** the plan is frozen (Interview, Design, Rubberduck generation, AVM version bumps, template diff summarization) or **after** apply completes (Drift triage, Cost anomaly detection, Firewall change composition). The apply path remains human-governed, with agents enhancing decision-making through prose summaries, compliance explainers, and regression detection. Priority automation candidates: **WA-2** (plan summarizer), **IA-1** (AVM version-bump PRs), **WA-5** (rubberduck generator), **WA-1** (drift triage), **IA-4** (cost guardrails), **IA-6** (ALZ conformance explainer). All respect the 5 hard guardrails, route through existing playbooks (05, 06, 02), and undergo deterministic verification (CI checks, policy enforcement). The 11-workflow pipeline already has agentic hooks (`copilot-setup-steps.yml`, `squad.yml`); new automation extends these patterns without bypassing human review gates.

---

**Report complete. Ready for team review and roadmap prioritization.**
