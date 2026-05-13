# SRE Agent Fit Analysis — Agentic ALZ

**Author:** Bobbie (Security Engineer)  
**Date:** 2026-05-12  
**Context:** Evaluating whether an SRE agent role belongs on the squad, and inventorying NetSec/ops automation candidates that fit the agentic model.

---

## Executive Summary

**Recommendation: (c) Skip SRE agent for v1 — add incremental automation without a dedicated agent.**

Agentic ALZ is architected as a deterministic GitOps pipeline with **narrow LLM stages** at specific decision points (Interview, Design, Drift Triage, Firewall Composer). Most traditional SRE concerns are either (a) already covered by deterministic workflows (drift detection, cost reporting) or (b) too judgment-heavy and context-dependent to safely automate via an LLM within the project's guardrail model.

Adding a dedicated SRE agent would expand the LLM surface beyond the consensus plan's boundaries without delivering sufficient bounded value. However, several **incremental, deterministic SRE-shaped automations** can be added to existing workflows or as new read-only stages without requiring a new squad member.

---

## 1. Traditional SRE Concerns → Agentic Fit Map

| SRE Concern | Fit Assessment | Rationale |
|-------------|----------------|-----------|
| **Incident triage** (read alerts, propose runbook step + IcM ticket) | **RISKY** | Alert semantics are context-dependent; runbook selection requires understanding of blast radius, current on-call state, and recent change history. High risk of hallucinated steps or inappropriate escalation. The existing incident playbook (`09-incident-response.md`) is designed for human commanders. |
| **Postmortem drafting** (read incident artifacts, draft 5-whys + action items) | **GOOD FIT** | Narrow input (incident issue, timeline, PR links) → structured output (5-whys template, action-item checklist). LLM proposes, human reviews and commits. Could be a future orchestrator stage: `stages/postmortem_draft.py`. |
| **Runbook synthesis from architecture diff** | **GOOD FIT** | Deterministic input (Terraform plan diff, ADR) → advisory output (runbook markdown with "if drift appears in X, check Y"). Read-only, no mutations. |
| **SLO/SLI definition from a new template** | **OUT-OF-SCOPE** | ALZ v1 does not ship with workload-level monitoring. SLO/SLI belongs to the workload repos, not the platform orchestrator. Defer to v2 or workload-agent surface. |
| **On-call alert deduplication & summarization** | **RISKY** | Requires live integration with an alerting system (Azure Monitor, Sentinel, PagerDuty) not in the MCP allowlist. Alert deduplication is brittle without tuning per-environment baselines. |
| **Capacity planning** (read consumption telemetry, propose right-sizing) | **GOOD FIT** | Read-only Azure Monitor / Cost Management API calls → advisory report. Could chain with the existing `cost.yml` workflow. NetSec review required if adding a new MCP server for Azure Monitor. |
| **Cost anomaly detection + advisory PR** | **GOOD FIT** | Deterministic cost-spike detection (threshold-based) + LLM-drafted issue or advisory comment. Extends the existing `cost.yml` workflow. No mutations; opens issues only. |
| **Security alert triage** (Defender for Cloud, Sentinel) | **RISKY** | Alert classification is judgment-heavy. False-negative (dismissing a real alert) has high cost. Defender findings span CVEs, misconfigs, threat intel; each requires domain knowledge to triage. Better served by deterministic severity routing + human review. |
| **Compliance evidence collection** (ASB, CIS, ISO) | **GOOD FIT** | Read-only: query Azure Policy compliance states, RBAC audit logs, resource configurations. Output: evidence bundle (JSON + markdown summary) for auditor review. Could be a `stages/compliance_snapshot.py`. |
| **Threat modeling for new Terraform templates** | **RISKY** | Threat modeling requires adversarial thinking ("what could an attacker do with this public IP + NSG rule?"). LLMs are prone to missing edge cases or hallucinating mitigations. The existing `stages/risk.py` is deterministic and auditable; expanding it with an LLM stage risks false confidence. |
| **Patch/version-bump triage** (OS images, k8s versions, etc.) | **GOOD FIT** | Separate from AVM module bumps. Read CVE databases, compare deployed image SKUs → advisory issue ("VM Scale Set X is on Ubuntu 22.04.3; 22.04.5 addresses CVE-YYYY-ZZZZ"). Deterministic + LLM summary = good fit. |
| **Resource decommissioning safety check** | **RISKY** | High blast radius if wrong. Requires understanding of dependencies (NSG → subnet → VNet, KeyVault → 50 workloads), downstream impact, and backup/state implications. Better served by deterministic dependency graph + human confirmation. |
| **Privileged access review automation** | **GOOD FIT** | Read-only RBAC audit: list Owner/UAA/Contributor assignments, compare to baseline, flag anomalies. The threat model already mentions `operate/rbac_drift.py` — this is an expansion. LLM drafts the summary; NetSec reviews. |

### Summary Table

- **GOOD FIT (7):** Postmortem drafting, runbook synthesis, capacity planning, cost anomaly detection, compliance evidence, patch triage, privileged access review  
- **RISKY (5):** Incident triage, alert deduplication, security alert triage, threat modeling, resource decommissioning  
- **OUT-OF-SCOPE (1):** SLO/SLI definition (workload-level, not platform-level)

---

## 2. SRE Agent: Yes/No/How?

### Recommendation: **(c) Skip — SRE concerns are out of scope for Agentic ALZ v1.**

#### Why Skip?

1. **Philosophy mismatch.** The consensus plan explicitly states: "Agentic ALZ is a deterministic GitOps pipeline orchestrator with a small number of narrow LLM-powered stages." SRE activities span a wide surface (alerts, incidents, capacity, compliance, patching) — adding an agent would create a sprawling role that violates the "narrow LLM stage" principle.

2. **Coverage already adequate.** The two highest-value Day-2 SRE tasks — drift detection and cost reporting — are already implemented as deterministic scheduled workflows (`drift.yml`, `cost.yml`). Incident response has a mature playbook (`09-incident-response.md`) and a CI-enforced gate. The remaining gaps (postmortem drafting, compliance snapshots, patch triage) can be added incrementally as **new deterministic stages or workflow extensions** without a dedicated agent.

3. **Risk concentration.** A general-purpose "SRE agent" would own too many judgment-heavy surfaces (incident triage, alert classification, threat modeling). The project's safety model depends on narrow, schema-validated input/output contracts at each LLM stage. An SRE agent with broad mandate would be hard to constrain.

4. **No clear owner.** The squad is themed on *The Expanse*. The natural SRE pick would be "Drummer" (Camina Drummer, Belter leader, ops-focused). However, **Drummer's role in the show is coordination and consensus-building, not autonomous ops** — which aligns poorly with autonomous SRE actions. The thematic fit is weak.

#### What We Lose by Not Having Dedicated SRE Coverage

- **Postmortem velocity.** Manual postmortem drafting is slow. An LLM-assisted postmortem stage could accelerate RCA documentation from "5 days to write" (per `incident-response.md`) to "5 hours to review." This is a real loss but not a v1 blocker.
  
- **Compliance audit prep.** Compliance evidence collection (Azure Policy states, RBAC logs, resource configs) is tedious and error-prone when done manually. An automated compliance snapshot stage would reduce auditor prep time from weeks to hours. Again, valuable but not v1-critical.

- **Proactive capacity signals.** Capacity planning is currently reactive (humans notice slowness, open a ticket). A proactive capacity-planning stage could flag "VM Scale Set X is at 80% CPU for 7 days" and propose right-sizing before a human notices. This is a quality-of-life improvement, not a safety issue.

#### Alternative: Incremental Automation Without an Agent

Instead of adding an SRE squad member, **extend the orchestrator with new deterministic stages** and **enrich existing workflows** (`drift.yml`, `cost.yml`) with optional LLM-assisted summaries. These stages are owned collectively by the existing squad, gated by the same guardrails (frontier-model allowlist, MCP allowlist, schema validation, rubberduck).

**Proposed incremental additions (no agent required):**

| Stage / Workflow Extension | Owner | Notes |
|----------------------------|-------|-------|
| `stages/postmortem_draft.py` | Holden (team lead) | Reads incident issue, emits 5-whys + action-item checklist. Human reviews and commits. |
| `stages/compliance_snapshot.py` | Bobbie (NetSec) | Reads Azure Policy compliance states, RBAC audit logs. Emits evidence bundle for auditors. |
| `stages/patch_triage.py` | Holden or Amos | Reads VM/AKS image SKUs, queries CVE databases, flags outdated images. Advisory only. |
| `cost.yml` enhancement | Amos (infra) | Add LLM-assisted anomaly summary to existing cost workflow. Opens issues on WoW spike > threshold. |
| `drift.yml` enhancement | Amos (infra) | Add optional `stages/runbook_hint.py` that reads drift diff and suggests runbook steps. Comment on drift issues. |
| `workflows/rbac-audit.yml` (new) | Bobbie (NetSec) | Monthly RBAC audit: list Owner/UAA/Contributor, compare to baseline, flag anomalies. Read-only. |

All of the above are **narrow, schema-validated, read-only stages** that fit within the existing guardrail model. None require a new squad member.

---

## 3. NetSec/Firewall Automation Expansion

### Beyond the Existing Firewall Composer

The roadmap item `llm-firewall-composer-stage` (deferred from v1) proposes RCG PRs against `alz-firewall-policy/lib`. Additional firewall-policy automations that fit the agentic model:

| Automation | Fit | Notes |
|------------|-----|-------|
| **Rule-collection conflict detection** | **GOOD FIT** | Deterministic: parse all RCGs, check for overlapping CIDR blocks, duplicate ports, or priority collisions. Emit report. Could be an OPA policy extension (`policies/firewall_conflicts.rego`). |
| **Effective-route-table summarization** | **GOOD FIT** | Read-only Azure Network Watcher API: resolve effective routes for a given subnet. LLM summarizes "traffic from subnet X to destination Y will egress via Azure Firewall Z." Advisory report for NetSec review. |
| **Firewall log triage** | **RISKY** | Firewall logs are high-volume and noisy. Automated triage risks false-negatives (missing a real intrusion attempt). Better served by Sentinel playbooks (out of scope for Agentic ALZ). |
| **Suspect-rule discovery** | **GOOD FIT** | Read-only: scan deployed RCGs for rules allowing `0.0.0.0/0` destinations, wildcards, or public IP ranges not in an allowlist. Flag for NetSec review. Extends `policies/firewall_rules.rego` logic. |
| **Least-privilege NSG synthesis** | **RISKY** | Proposing NSG rules requires understanding of workload traffic patterns, which the platform orchestrator does not have. Better deferred to workload-specific agents. |
| **Firewall policy version diff** | **GOOD FIT** | Read-only: compare two versions of `alz-firewall-policy/lib/<pattern>/rcg.json`, emit a human-readable diff. Useful for NetSec review of Composer PRs. Could be a GitHub Action triggered on PR open. |
| **Rule usage analytics** | **GOOD FIT** | Read Azure Firewall logs (requires new MCP server or Azure Monitor integration): report which rules have 0 hits over 30 days. NetSec can prune dead rules. Read-only, advisory. |

**High-value next steps (NetSec ownership):**

1. **Add `policies/firewall_conflicts.rego`** — deterministic conflict detection gating firewall PRs. No LLM, pure Rego logic.
2. **Add `stages/firewall_effective_routes.py`** — read-only Network Watcher integration, LLM-assisted summary for NetSec review.
3. **Add `stages/suspect_rule_scan.py`** — nightly scan of deployed RCGs, flags suspicious rules (0.0.0.0/0, wildcards not in allowlist). Opens issues.
4. **Add `workflows/firewall-rule-usage.yml`** — monthly workflow querying Azure Firewall logs, reports 0-hit rules. Requires new MCP server or direct Azure SDK call (NetSec approval required).

All of the above are **read-only or deterministic policy checks**, fitting the project's safety model.

---

## 4. MCP Write-Mode Ops Workflows

### Current State

- **`github-mcp`** is the only server with `mode: write`.
- Tool list is restricted to PR/issue surface: `pull_requests.create`, `issues.create`, `issues.add_comment`, etc.
- Deliberately excluded: `repos.create_or_update_file`, `actions.dispatch_workflow`, `environments.approve_deployment`.
- OPA policy enforces: no `write` without a `netsec_approval` block.

### What Ops Workflows Could Safely Raise Write-Mode Gates?

| Workflow | Write-Mode Justification | Guardrails Required |
|----------|-------------------------|---------------------|
| **Azure Policy remediation task trigger** | Policy remediation tasks (e.g., "append NSG rule to all VNets missing it") are a native Azure feature. An MCP server that triggers (but does not define) remediation tasks is lower-risk than one that mutates resources directly. | • New MCP server `azure-policy-remediation-mcp` with single tool `policy.trigger_remediation_task`. <br>• NetSec approval required. <br>• OPA policy: remediation tasks MUST target policy assignments already deployed by Terraform, never ad-hoc policies. <br>• Audit log: every trigger logged with policy ID + initiator. |
| **GitHub environment approval** (for lab/sandbox only) | The `prod` environment must remain human-gated. However, a `sandbox` environment approval gate could be auto-approved by an LLM stage if the plan passes all OPA policies and the risk score is below a threshold. | • `github-mcp` tool `environments.approve_deployment` added BUT restricted to `sandbox` environment only via OPA policy. <br>• NetSec approval + policy enforcement: `approve_deployment` calls MUST include `environment == "sandbox"` in the OPA input. <br>• Human override: maintainers can still manually approve. |
| **Cost-quota enforcement** (resource group locks) | If a workload exceeds its monthly cost quota, lock the resource group to prevent further spend. This is a write operation (Azure Management Locks API) but is a safety control, not a mutation of the workload itself. | • New MCP server `azure-mgmt-locks-mcp` with tools `locks.create`, `locks.delete`. <br>• Write-mode restricted to `CanNotDelete` locks only (not `ReadOnly`). <br>• OPA policy: locks may only be placed on resource groups tagged with `CostQuotaEnforced=true` and only after the quota threshold is breached (logged in Cost Management). <br>• NetSec approval required. |
| **Drift auto-remediation** (limited scope) | Auto-remediate "safe" drift: tag changes, description field updates, non-critical metadata. Leave resource-level drift for human review. | • **HIGH RISK.** Defining "safe" drift is context-dependent. A tag change on a firewall rule collection could be a security signal (someone manually tweaking prod). <br>• If pursued: require an allowlist of "safe" resource types + attributes (OPA policy), NetSec approval, and mandatory rubberduck on every remediation PR. <br>• Recommend: defer to v2, keep drift read-only for v1. |

### What Should NEVER Be Write-Mode?

| Surface | Why Never Write-Mode |
|---------|---------------------|
| **`terraform apply` via MCP** | Apply is the highest blast-radius operation in the repo. It MUST remain a CI job consuming an immutable saved plan artifact in the protected `prod` environment. No LLM or MCP server should ever invoke `terraform apply`. |
| **Direct Azure resource mutation** | An MCP server that can call `PUT /subscriptions/{id}/resourceGroups/{rg}/providers/Microsoft.Compute/virtualMachines/{vm}` bypasses Terraform state, creating invisible drift. All Azure mutations MUST flow through Terraform. |
| **OIDC credential rotation** | Federated credentials are identity-layer. Rotating them via an MCP server would allow an attacker to lock out CI by rotating to a non-existent GitHub environment. Keep this operation manual + break-glass only. |
| **State file mutation** | The state backend is RBAC-only, no shared keys. An MCP server with write access to the state container could silently corrupt or delete state. Keep state access strictly to the `alz-apply-*` identities federated to the `prod` environment. |
| **Kill switch override** | The kill switch (`AGENTIC_ALZ_DISABLED`) is checked at the top of every workflow and every orchestrator stage. An MCP server that can unset the repo variable would defeat the emergency shutdown path. |

**Summary:** Write-mode MCP servers are acceptable for **advisory mutations** (issue/PR creation, sandbox environment approvals, policy remediation task triggers) with strong OPA gating. Write-mode is **never** acceptable for destructive paths (apply, direct Azure mutations, identity rotation, state access, kill switch).

---

## 5. Cross-Cutting Concerns — NetSec Block/Constrain List

Features the other squad agents (Naomi, Amos, Alex) might propose that Bobbie (NetSec) would **BLOCK** or **constrain**:

| Proposed Feature | Agent Who Might Propose | NetSec Position | Guardrails Required |
|------------------|-------------------------|----------------|---------------------|
| **"Let's add a Sentinel content generator stage"** | Naomi (Design) | **BLOCK for v1.** Sentinel analytics rules (KQL queries) are security-critical. Hallucinated KQL can miss real attacks (false negative) or cause alert fatigue (false positive). Both are high-cost. Sentinel content belongs in a dedicated repo with SOC review, not in the platform orchestrator. | N/A (blocked). Defer to v2 with SOC-staffed review. |
| **"Let's add a Stage that proposes NSG rules based on traffic logs"** | Amos (Infra) | **CONSTRAIN.** Traffic-log-driven NSG synthesis is valuable BUT requires understanding of legitimate vs. attacker-sourced traffic. Constraint: the stage MUST be read-only (proposes NSG diff as a PR), MUST schema-validate the NSG rule JSON, and MUST flag any rule allowing public IP ranges for mandatory NetSec review. | • New schema `schemas/nsg.schema.json`. <br>• OPA policy: any NSG rule with `source_address_prefix` containing a public CIDR or `*` triggers NetSec CODEOWNER review. <br>• The stage is a future roadmap item, not v1. |
| **"Let's allow the Drift Triage stage to auto-merge 'safe' drift PRs"** | Alex (Operate) | **BLOCK.** Drift PRs have passed through Terraform plan, so they are syntactically valid — but semantic safety ("is this drift benign?") requires context the LLM does not have. A tag change on a firewall could be a security signal. Keep drift PRs human-reviewed. | N/A (blocked). All drift PRs require human merge. |
| **"Let's add a Stage that queries Microsoft Graph for Entra ID group membership and proposes RBAC assignments"** | Holden (Lead) | **CONSTRAIN.** Entra ID → Azure RBAC bridging is legitimate (e.g., "assign the 'Platform-Contributors' Entra group to Contributor on the platform MG"). Constraint: the stage MUST emit Terraform `azurerm_role_assignment` resources (not Azure CLI calls), MUST validate against `policies/rbac.rego` (to be written), and MUST flag any Owner or UAA assignment for mandatory NetSec review. | • New MCP server `microsoft-graph-mcp` (read-only: `groups.list`, `groups.get_members`). <br>• New OPA policy `policies/rbac.rego`: denies Owner/UAA assignments unless justified in a comment block. <br>• NetSec CODEOWNER on any PR touching RBAC assignments. |
| **"Let's allow the Firewall Composer to auto-merge lib/ PRs if they only add rules, never modify existing ones"** | Bobbie (self-proposal, advocating for velocity) | **CONSTRAIN (self-review).** "Add-only" PRs are lower-risk than "modify" PRs, but they still have blast radius (a badly-formed rule can block legitimate traffic). Constraint: auto-merge is acceptable IF the PR passes (a) `policies/firewall_rules.rego`, (b) `policies/firewall_conflicts.rego` (new), (c) eval harness with a golden firewall run, AND (d) is labeled `auto-merge-eligible` by a human NetSec reviewer clicking a button. The label gates merge, not the stage itself. | • GitHub Action: `workflows/firewall-automerge-gate.yml` checks for label + passing CI. <br>• Label `auto-merge-eligible` can only be applied by NetSec CODEOWNERS. <br>• Automerge fires only after 24-hour soak (gives time for rollback if needed). |
| **"Let's add a Stage that scans Docker images in ACR and opens CVE remediation PRs"** | Amos (Infra) | **ALLOW with constraints.** Container image scanning is well-scoped: query ACR for images, query Trivy/Grype for CVEs, emit a Terraform diff that bumps the `image` attribute. Constraints: the stage is read-only (opens PRs), MUST validate the new image tag exists in ACR, and MUST NOT propose `:latest` tags (OPA policy forbids them). | • New MCP server `azure-acr-mcp` (read-only: `repositories.list`, `manifests.list`). <br>• OPA policy: `:latest`, `:master`, and untagged images are denied. <br>• Eval harness: golden run with a CVE-remediation PR proves the schema works. |

**Summary:** NetSec will **block** features that expand the LLM surface into judgment-heavy security domains (Sentinel, auto-merge of drift, SAP-assignments without review). NetSec will **constrain** features that touch security surfaces but have clear deterministic bounds (NSG rule proposals, RBAC assignments, firewall add-only PRs) by requiring schema validation, OPA gating, and human-in-the-loop review.

---

## 6. Synthesis and Recommendations

### For the Project Lead (Holden)

1. **Do not add an SRE squad member for v1.** The role would be sprawling and hard to constrain. Stick to the consensus plan's "narrow LLM stages" philosophy.

2. **Add incremental SRE-shaped stages** to the orchestrator as they prove necessary:
   - `stages/postmortem_draft.py` (post-incident velocity boost)
   - `stages/compliance_snapshot.py` (auditor prep time reduction)
   - `stages/patch_triage.py` (proactive CVE flagging)
   
   These are **owned collectively** by the squad, gated by the same guardrails.

3. **Enrich existing workflows** (`drift.yml`, `cost.yml`) with optional LLM-assisted summaries before adding new workflows.

### For NetSec (Bobbie)

1. **Firewall automation roadmap:**
   - Add `policies/firewall_conflicts.rego` (deterministic, no LLM).
   - Add `stages/suspect_rule_scan.py` (read-only, LLM summary).
   - Defer firewall log triage (too noisy) and least-privilege NSG synthesis (workload-specific) to v2.

2. **MCP write-mode stance:**
   - Azure Policy remediation task triggers: acceptable with OPA gating + audit log.
   - Sandbox environment auto-approval: acceptable with OPA policy restricting to `sandbox` only.
   - Drift auto-remediation: **defer to v2**, too much risk of false-safe classification.
   - Terraform apply via MCP: **never**.

3. **Cross-cutting blocks:**
   - Sentinel content generation: blocked for v1.
   - Drift PR auto-merge: blocked.
   - RBAC/firewall proposals: constrained via schema + OPA + CODEOWNER review.

---

## Appendices

### A. RBAC Drift Detector (Mentioned in Threat Model)

The threat model references `orchestrator/agentic_alz/operate/rbac_drift.py` but it does not exist yet. **Proposed implementation (deterministic, no LLM):**

```python
"""RBAC drift detector — flags Owner/UAA/Contributor anomalies.

Reads Azure RBAC role assignments via azure-mcp (read-only), compares to a
baseline (checked into the repo or stored in the state backend), flags:
  - New Owner or User Access Administrator assignments.
  - Contributor assignments on management group or subscription scope that are
    not in the baseline.
  - Service principal role assignments with expired credentials.

Emits a GitHub issue with the diff. Never auto-remediates.
"""
```

**Add to ROADMAP.md as a Phase 3 item (deterministic workflow, agent-eligible).**

### B. Compliance Snapshot Schema

`schemas/compliance.schema.json` would type the output of `stages/compliance_snapshot.py`:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["schema_version", "snapshot_date", "policies", "rbac", "resources"],
  "properties": {
    "schema_version": {"const": "1"},
    "snapshot_date": {"type": "string", "format": "date-time"},
    "policies": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "compliance_state"],
        "properties": {
          "name": {"type": "string"},
          "compliance_state": {"enum": ["Compliant", "NonCompliant", "Unknown"]},
          "non_compliant_resources": {"type": "integer"}
        }
      }
    },
    "rbac": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["principal", "role", "scope"],
        "properties": {
          "principal": {"type": "string"},
          "role": {"type": "string"},
          "scope": {"type": "string"}
        }
      }
    },
    "resources": {
      "type": "object",
      "properties": {
        "total": {"type": "integer"},
        "by_type": {"type": "object"}
      }
    }
  }
}
```

### C. Postmortem Draft Prompt Outline

`prompts/postmortem.v1.md` would be a narrow LLM prompt:

**Inputs:**
- Incident issue URL (from GitHub)
- Timeline (scraped from incident issue comments)
- PR links (the fix that landed)
- Pre-incident state (Terraform plan or Azure resource snapshot)

**Output:**
- 5-whys analysis (structured, each "why" cites evidence)
- Action items (checklist: add OPA rule, update runbook, rotate credential)
- Suggested ADR (if the incident revealed an architectural gap)

**Guardrails:**
- Input: schema-validated, max 4096 chars per field (prompt-injection guard)
- Output: schema-validated against `schemas/postmortem.schema.json`
- Human: reviews and commits to `docs/incidents/YYYY-MM-DD-shortname.md`

### D. Threat Model Update — Residual Risk Addition

Add to `docs/threat-model.md` § *Residual risks accepted in v1*:

> - **SRE automation gaps.** Incident triage, alert classification, and threat
>   modeling are currently human-only. Automating these via LLM would require
>   prohibitively strong guardrails (multi-model judge per decision, schema-
>   validated tooling, NetSec review per output). The project accepts manual
>   SRE workflows for v1 to keep the LLM surface narrow.

---

## References

- `AGENTS.md` — canonical agent-instruction surface, defines "narrow LLM stages" philosophy.
- `docs/consensus-plan.md` § 1 — "Agentic ALZ is a deterministic GitOps pipeline orchestrator with a small number of narrow LLM-powered stages."
- `docs/incident-response.md` — existing incident playbook; human-driven.
- `docs/threat-model.md` — mentions `orchestrator/agentic_alz/operate/rbac_drift.py` (not yet implemented).
- `policies/mcp_allowlist.rego` — OPA policy enforcing NetSec approval for write-mode MCP servers.
- `.github/workflows/drift.yml`, `.github/workflows/cost.yml` — existing Day-2 deterministic workflows.
- *Google SRE Book — Eliminating Toil*. Retrieved 2026-05-08. <https://sre.google/sre-book/eliminating-toil/>
- *NIST SP 800-53 Rev. 5 — Security and Privacy Controls*. AU (Audit and Accountability) family justifies RBAC drift detection and compliance snapshots. Retrieved 2026-05-08. <https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final>

---

**End of Report.**
