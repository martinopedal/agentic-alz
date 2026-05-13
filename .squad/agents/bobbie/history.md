# Bobbie — History

**Project:** Agentic ALZ — deterministic GitOps pipeline for Azure Landing Zones (ALZ Accelerator + AVM + Terraform), with narrow LLM stages (Interview, Design, Drift Triage, Firewall Composer). Apply is never an LLM action.
**Stack:** Python 3 (orchestrator), Terraform/AVM (templates), OPA Rego (policies), GitHub Actions, MCP, frontier LLMs
**Repo:** martinopedal/agentic-alz
**Lead user:** martinopedal
**Cast at:** 2026-05-12T22:36:05Z

## Core Context

- NetSec CODEOWNER for `firewall-policy/**` and the sibling `alz-firewall-policy` repo.
- MCP write-mode never auto-allowed: `policies/mcp_allowlist.rego` refuses any `write` entry without a `netsec_approval` block.
- `github-mcp` is permanently restricted to PR/issue tool surface — may never trigger an apply.
- RCG schema tests: `orchestrator/tests/test_rcg_schema.py` parametrizes over all `firewall-policy/lib/*/rcg.json` fixtures.

## Learnings

(append below — newest at top)

### 2026-05-12T23:21:00Z: SRE Agent Fit Analysis

**Task:** Evaluated whether an SRE agent role belongs on the squad. Mapped 13 traditional SRE concerns (incident triage, postmortem drafting, capacity planning, security alert triage, compliance evidence collection, patch triage, privileged access review, etc.) to agentic fit (GOOD FIT / RISKY / OUT-OF-SCOPE).

**Key findings:**
- **7 GOOD FIT:** Postmortem drafting, runbook synthesis, capacity planning, cost anomaly detection, compliance evidence collection, patch triage, privileged access review — all narrow input/output, read-only or advisory.
- **5 RISKY:** Incident triage, alert deduplication, security alert triage, threat modeling, resource decommissioning — all judgment-heavy, context-dependent, or high blast radius on false-negative.
- **1 OUT-OF-SCOPE:** SLO/SLI definition (workload-level, not platform orchestrator concern).

**Recommendation: (c) Skip SRE agent for v1.** The consensus plan's "narrow LLM stages in a deterministic pipeline" philosophy means SRE concerns are better addressed as incremental automation (new stages like `postmortem_draft.py`, `compliance_snapshot.py`, `patch_triage.py`) owned collectively by the squad, rather than a sprawling SRE agent role.

**NetSec automation candidates identified:**
- Firewall: `policies/firewall_conflicts.rego` (deterministic conflict detection), `stages/suspect_rule_scan.py` (0.0.0.0/0 scanner), `stages/firewall_effective_routes.py` (Network Watcher integration), firewall rule usage analytics.
- MCP write-mode: Azure Policy remediation task triggers (acceptable with OPA gating), sandbox environment auto-approval (acceptable with env restriction), drift auto-remediation (DEFER — too risky).
- Cross-cutting blocks: Sentinel content generation (blocked for v1), drift PR auto-merge (blocked), RBAC/firewall proposals (constrained via schema + OPA + CODEOWNER).

**Threat model residual risk:** SRE automation gaps (incident triage, alert classification, threat modeling) remain human-only for v1 to keep the LLM surface narrow.

**What we lose by skipping SRE agent:** Postmortem velocity (5 days manual → 5 hours LLM-assisted), compliance audit prep speed, proactive capacity signals. All valuable but not v1-critical.

**References:** Consensus plan § 1 (deterministic pipeline), incident-response.md (human-driven playbook), threat-model.md (RBAC drift detector mentioned but not implemented), mcp_allowlist.rego (write-mode NetSec approval), Google SRE Book (eliminating toil), NIST SP 800-53 Rev. 5 (AU family for audit/compliance).

---

### 2026-05-13: Roadmap assignments — Phase 3 agentic features

**Assigned items (priority rank):**
8. Rego Unit-Test Generation (rank 8) - Plan stage, LLM-assisted policy test synthesis
10. Compliance Snapshot (rank 10) - Day-2, monthly evidence collection for auditors

**Implementation order:** Rego Unit-Test Gen (immediate, high policy coverage impact), Compliance Snapshot (post-v1 or concurrent, requires new schemas/compliance contract).

**Pattern for Rego tests:** On policy change, LLM reads .rego file + docstring, generates _test.rego with PASS/DENY fixtures. `opa test policies/ -v` verifies deterministically. Human reviews before merge. Touches policies/ — human-only per AGENTS.md.

**Pattern for Compliance Snapshot:** `stages/compliance_snapshot.py` reads Azure Policy compliance states and RBAC audit logs via azure-mcp (read-only). Output validates against `schemas/compliance.schema.json`. Emits evidence bundle (JSON + markdown summary) for auditor review. Monthly scheduled workflow opens issue with summary. Touches schemas/ — human-only per AGENTS.md.

**Infrastructure ownership:** Bobbie also owns firewall_conflicts.rego (deterministic policy, no LLM) as Phase 3 supporting item.

**Interdependency:** Rego Unit-Test Gen is independent. Compliance Snapshot requires schema design (deferred pending martinopedal confirmation of pattern).
