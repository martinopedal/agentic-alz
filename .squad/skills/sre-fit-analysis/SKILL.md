# Skill: SRE Fit Analysis for Agentic Systems

**Skill ID:** `sre-fit-analysis`  
**Owner:** Bobbie (Security Engineer)  
**Created:** 2026-05-12  
**Last Updated:** 2026-05-12

---

## Purpose

Evaluate whether a dedicated SRE agent role belongs on an agentic system team, or whether SRE concerns are better addressed through incremental deterministic automation. Produces a structured fit map (GOOD FIT / RISKY / OUT-OF-SCOPE) for traditional SRE concerns and a recommendation (add agent / extend existing / skip).

---

## When to Use

- A project is considering adding an SRE or operations-focused agent to a squad.
- The project already has some Day-2 automation (drift detection, cost reporting) but gaps remain (incident response, capacity planning, compliance).
- The project has a philosophy or constraint on LLM surface expansion (e.g., "narrow LLM stages only").

---

## Inputs

1. **Project philosophy statement** — what is the project's stance on LLM automation vs. deterministic automation? (e.g., "narrow LLM stages in a deterministic pipeline")
2. **Existing Day-2 automation inventory** — what workflows already exist? (drift detection, cost reporting, incident playbooks, alert integrations)
3. **Guardrail model** — what gates exist on LLM usage? (model allowlist, MCP allowlist, schema validation, multi-model judge, rubberduck)
4. **SRE concern list** — which traditional SRE activities are in scope for evaluation? (incident triage, postmortem drafting, capacity planning, alert deduplication, security alert triage, compliance evidence collection, patch triage, privileged access review, runbook synthesis, resource decommissioning, threat modeling, etc.)

---

## Process

### Step 1: Map SRE Concerns to Agentic Fit

For each SRE concern, classify as:

- **GOOD FIT:** Narrow input/output, read-only or advisory, deterministic boundaries, schema-validatable. Examples: postmortem drafting (incident issue → 5-whys template), compliance evidence collection (Azure Policy states → evidence bundle), patch triage (deployed image SKUs → CVE flag report).
  
- **RISKY:** Judgment-heavy, context-dependent, high blast radius on false-negative, or requires adversarial thinking. Examples: incident triage (alert semantics vary by environment), security alert triage (false-negative = missed attack), threat modeling (adversarial creativity), resource decommissioning (dependency graphs are complex).

- **OUT-OF-SCOPE:** Belongs to a different layer (workload-level vs. platform-level) or requires integration with systems not in scope. Examples: SLO/SLI definition (workload concern, not platform orchestrator concern).

**Output:** A table with 3 columns: SRE Concern | Fit Assessment | Rationale.

### Step 2: Evaluate Coverage Gaps

Compare the GOOD FIT list to existing automation. Which GOOD FIT concerns are already covered by deterministic workflows? Which are not?

**Output:** A coverage matrix: Concern | Existing Coverage | Gap.

### Step 3: Recommend One of Three Options

- **(a) Add a new squad member** who owns SRE-shaped agentic stages. Describe their charter (role name, badge, what they own, what they MUST NOT do).
  
- **(b) Add SRE-shaped stages to the orchestrator without a new squad member.** Describe which stages (e.g., `postmortem_draft.py`, `compliance_snapshot.py`) and which existing agent owns them.

- **(c) Skip.** SRE concerns are out of scope for this project today. Justify what is lost by not having coverage (velocity, proactive signals, audit prep time).

**Selection criteria:**
- If >= 5 GOOD FIT concerns are uncovered AND the project philosophy permits LLM expansion, consider (a).
- If 2-4 GOOD FIT concerns are uncovered AND they can share schemas/guardrails with existing stages, consider (b).
- If most concerns are RISKY or already covered, recommend (c).

### Step 4: Cross-Cutting Analysis

Identify features other agents might propose that the SRE/ops owner would BLOCK or CONSTRAIN on reliability or security grounds. Examples:
- Auto-merge of drift PRs (BLOCK: drift semantic safety requires context)
- Sentinel content generation (BLOCK: KQL false-negatives are high-cost)
- NSG rule proposals (CONSTRAIN: require schema validation + NetSec review on public IP ranges)

**Output:** A table: Proposed Feature | Agent Who Might Propose | Position (BLOCK / CONSTRAIN) | Guardrails Required.

---

## Outputs

1. **SRE Fit Map** (table): SRE Concern → Fit Assessment → Rationale
2. **Coverage Gap Analysis** (table): Concern → Existing Coverage → Gap
3. **Recommendation** (one of a/b/c) with one-paragraph justification
4. **Cross-Cutting Concerns** (table): Proposed Feature → Position → Guardrails
5. **Supporting Report** (markdown): Full analysis with references, appendices (sample schemas, prompt outlines, policy suggestions)

---

## Example Application

See `.squad/log/research/bobbie-sre-and-ops.md` for a worked example on the Agentic ALZ project.

**Summary of that example:**
- **13 SRE concerns evaluated:** 7 GOOD FIT, 5 RISKY, 1 OUT-OF-SCOPE.
- **Existing coverage:** Drift detection (deterministic), cost reporting (deterministic), incident playbook (human-driven).
- **Recommendation:** (c) Skip SRE agent. Add incremental stages (`postmortem_draft.py`, `compliance_snapshot.py`, `patch_triage.py`) owned collectively by the squad.
- **What we lose:** Postmortem velocity (5 days → 5 hours), proactive compliance audit prep, proactive capacity signals. All valuable but not v1-critical.
- **Cross-cutting blocks:** Sentinel content gen (blocked), drift auto-merge (blocked), RBAC/firewall proposals (constrained via schema + OPA).

---

## Reusability Notes

This skill is **project-agnostic** but assumes:
- The project has some form of LLM/agent involvement (not purely manual ops).
- The project has a stance on LLM surface expansion (either "expand freely" or "narrow stages only").
- SRE concerns are in-scope for the project (platform-level, not workload-only).

**Adaptations for other projects:**
- If the project has no existing Day-2 automation, all GOOD FIT concerns are gaps → stronger case for (a) or (b).
- If the project has no guardrail model, all concerns are RISKY until guardrails are added → recommend adding guardrails first, then re-evaluate.
- If the project is workload-focused (not platform-focused), swap "platform-level" concerns (drift, RBAC audit) for "workload-level" concerns (application performance monitoring, log aggregation).

---

## References

- *Google SRE Book — Eliminating Toil*. Definition of toil and criteria for automation candidates. <https://sre.google/sre-book/eliminating-toil/>
- *NIST SP 800-53 Rev. 5 — Security and Privacy Controls*. AU (Audit and Accountability) family justifies compliance snapshots and RBAC drift detection. <https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final>
- *OWASP Top 10 for LLM Applications (2025)*. Justifies the RISKY classification for security-critical automation (threat modeling, alert triage). <https://owasp.org/www-project-top-10-for-large-language-model-applications/>

---

**End of Skill Documentation.**
