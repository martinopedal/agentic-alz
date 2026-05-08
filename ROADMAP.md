# Agentic ALZ — Roadmap

This file is the **single source of truth** for planned work. It is parsed by
[`scripts/squad_bootstrap.py`](scripts/squad_bootstrap.py), which upserts one
GitHub issue per item (keyed by an HTML-comment marker on the issue body) and
optionally assigns the Copilot cloud agent. See [`docs/squad.md`](docs/squad.md)
for the contract and governance rules.

Each H3 below is one roadmap item. The fenced ` ```yaml ` block underneath the
heading is its metadata, validated against
[`schemas/roadmap.schema.json`](schemas/roadmap.schema.json). Free-form prose
between the metadata block and the next H3 becomes the issue body's
"Context" paragraph; bullets under `acceptance_criteria` become the
"Acceptance criteria" checklist.

> **Eligibility default is opt-in.** `agent_eligible: false` keeps an item
> human-only. Anything touching `apply.yml`, `bootstrap/`, `policies/`,
> `prompts/`, `schemas/`, or `docs/models.allowlist.yaml` MUST stay
> `agent_eligible: false`.

---

## Phase 0 — Prerequisites

### Document and verify Phase-0 Azure prerequisites

```yaml
id: phase0-prereqs-doc
title: "Phase 0: document and verify Azure prerequisites"
milestone: "Phase 0 — Prerequisites"
labels: [area:bootstrap, type:docs, human-only]
agent_eligible: false
acceptance_criteria:
  - "docs/phase-0-prerequisites.md lists every tenant/subscription/role required before phase1.sh can run"
  - "Each prerequisite has a verification command (az CLI / Graph) the operator can run"
  - "Break-glass account requirements (hardware-key MFA, monitoring) are documented"
```

Phase 0 is the human-only ground truth. It must be audited by a human before
any pipeline activity. Listed for visibility; the bootstrap script will create
the tracking issue but never assign it to an agent.

### Establish hardened Terraform state backend

```yaml
id: phase0-state-backend
title: "Phase 0: stand up hardened Terraform state backend (mgmt sub)"
milestone: "Phase 0 — Prerequisites"
labels: [area:bootstrap, area:security, human-only]
agent_eligible: false
depends_on: [phase0-prereqs-doc]
acceptance_criteria:
  - "Azure Storage account in management subscription with CMK, private endpoint, soft-delete, versioning"
  - "RBAC-only access; shared keys disabled"
  - "One container per repo (agentic-alz, alz-platform, alz-firewall-policy)"
  - "Blob-lease locking verified end-to-end with `terraform init` + `plan`"
```

---

## Phase 1 — Bootstrap

### Implement Phase-1 idempotent bootstrap script

```yaml
id: phase1-bootstrap-script
title: "Phase 1: implement bootstrap/phase1.sh idempotent provisioning"
milestone: "Phase 1 — Bootstrap"
labels: [area:bootstrap, human-only]
agent_eligible: false
depends_on: [phase0-state-backend]
acceptance_criteria:
  - "Creates per-phase Entra ID workload identities (alz-readonly, alz-plan, alz-apply-platform, alz-apply-firewall, alz-vending)"
  - "Federates each identity to GitHub via OIDC; no PATs created"
  - "Idempotent: repeated runs are no-ops"
  - "Refuses to run if AGENTIC_ALZ_DISABLED is set"
```

Touches identity and bootstrap; stays human-driven by policy.

### Provision sibling repos (alz-platform, alz-firewall-policy, alz-workloads)

```yaml
id: phase1-sibling-repos
title: "Phase 1: provision sibling repos with CODEOWNERS and protections"
milestone: "Phase 1 — Bootstrap"
labels: [area:bootstrap, area:governance, human-only]
agent_eligible: false
depends_on: [phase1-bootstrap-script]
acceptance_criteria:
  - "alz-platform repo created with branch protection on main and required CI"
  - "alz-firewall-policy repo created with NetSec CODEOWNER on policies/base/ and lib/"
  - "alz-workloads/<sample> template repo demonstrates the workload shape"
  - "Each sibling repo has its own state container in the mgmt-sub backend"
```

---

## Phase 2 — Pipeline

### Wire validate workflow to gate every PR

```yaml
id: phase2-validate-workflow
title: "Phase 2: validate workflow runs fmt/validate/tflint/checkov/conftest on every PR"
milestone: "Phase 2 — Pipeline"
labels: [area:ci, area:terraform]
agent_eligible: true
depends_on: [phase1-sibling-repos]
acceptance_criteria:
  - ".github/workflows/validate.yml runs terraform fmt -check, validate, tflint, checkov, and conftest against templates/"
  - "Job fails closed when any tool exits non-zero"
  - "Kill switch (AGENTIC_ALZ_DISABLED) short-circuits the workflow"
  - "Eval harness exercise (python evals/replay.py) green"
```

Pure CI plumbing, no destructive paths — eligible for the Copilot agent.

### Wire plan workflow to produce immutable plan artifact

```yaml
id: phase2-plan-workflow
title: "Phase 2: plan workflow uploads immutable terraform plan artifact"
milestone: "Phase 2 — Pipeline"
labels: [area:ci, area:terraform]
agent_eligible: true
depends_on: [phase2-validate-workflow]
acceptance_criteria:
  - ".github/workflows/plan.yml runs `terraform plan -out=tfplan` and `terraform show -json` and uploads both as a workflow artifact"
  - "Plan artifact is content-addressed by SHA-256; SHA emitted to PR check summary"
  - "Apply workflow consumes only this artifact; never re-plans"
  - "Infracost diff posted as a PR comment"
```

### Apply workflow consumes saved plan only (deterministic CI)

```yaml
id: phase2-apply-workflow
title: "Phase 2: apply workflow consumes saved plan artifact in protected env"
milestone: "Phase 2 — Pipeline"
labels: [area:ci, area:security, human-only]
agent_eligible: false
depends_on: [phase2-plan-workflow]
acceptance_criteria:
  - "Runs only in the protected `prod` GitHub Environment"
  - "Refuses to apply if the saved plan SHA does not match the SHA on the PR"
  - "Refuses to apply if AGENTIC_ALZ_DISABLED is set"
  - "Re-runs `terraform plan` post-apply and fails the job on any drift"
```

Apply is the highest-blast-radius surface in the repo and is **never** an LLM
or agent action.

### Day-2 drift detector (read-only)

```yaml
id: phase2-drift-detector
title: "Phase 2: nightly drift detector opens issues, never auto-merges"
milestone: "Phase 2 — Pipeline"
labels: [area:ci, area:operate]
agent_eligible: true
depends_on: [phase2-apply-workflow]
acceptance_criteria:
  - "Scheduled workflow runs `terraform plan` against current state"
  - "Honours 2-hour post-apply cooldown (orchestrator/agentic_alz/operate/drift_cooldown.py)"
  - "Files an issue per drifted resource with the diff in the body"
  - "Never opens a PR or auto-remediates"
```

---

## LLM stages

### Interview stage — minimal-schema Q&A producing inputs.yaml

```yaml
id: llm-interview-stage
title: "LLM: Interview stage produces inputs.yaml validated by inputs.schema.json"
milestone: "LLM stages"
labels: [area:orchestrator, area:llm, human-only]
agent_eligible: false
depends_on: [phase2-validate-workflow]
acceptance_criteria:
  - "Interview prompt versioned under prompts/"
  - "Output validates against schemas/inputs.schema.json"
  - "Hand-edit of inputs.yaml is a first-class supported entry point"
  - "All LLM calls go through agentic_alz.llm.models.assert_frontier"
```

Touches `prompts/` and `schemas/` — sensitive surfaces, must stay human-driven
and gated by the multi-model judge.

### Design stage — ADR + design.json

```yaml
id: llm-design-stage
title: "LLM: Design stage emits ADR and typed design.json"
milestone: "LLM stages"
labels: [area:orchestrator, area:llm, human-only]
agent_eligible: false
depends_on: [llm-interview-stage]
acceptance_criteria:
  - "Design prompt versioned under prompts/"
  - "Output validates against schemas/design.schema.json"
  - "ADR written to docs/adr/ following docs/adr-template.md"
  - "Citations to microsoft-learn-mcp included in the ADR"
```

### Drift Triage stage — classify & summarise nightly drift

```yaml
id: llm-drift-triage-stage
title: "LLM: Drift Triage stage classifies and summarises nightly drift"
milestone: "LLM stages"
labels: [area:orchestrator, area:llm, human-only]
agent_eligible: false
depends_on: [phase2-drift-detector, llm-design-stage]
acceptance_criteria:
  - "Reads drift issues, emits a typed risk-classified summary"
  - "Never proposes a remediation PR"
  - "Token budget enforced via agentic_alz.budget"
```

### Firewall Change Composer stage — propose RCG PRs against lib/

```yaml
id: llm-firewall-composer-stage
title: "LLM: Firewall Change Composer proposes RCG PRs against alz-firewall-policy/lib"
milestone: "LLM stages"
labels: [area:orchestrator, area:llm, area:security, human-only]
agent_eligible: false
depends_on: [phase1-sibling-repos, llm-design-stage]
acceptance_criteria:
  - "Composer prompt versioned under prompts/"
  - "Opens PRs against alz-firewall-policy; never pushes to main"
  - "PR body includes the rule-collection diff and the inputs that produced it"
  - "NetSec CODEOWNER required to approve"
```

---

## Cross-cutting

### Eval harness gates CI with at least one golden run

```yaml
id: cross-eval-gating
title: "Eval harness: at least one golden run is required to gate CI"
milestone: "Cross-cutting"
labels: [area:ci, area:eval]
agent_eligible: true
depends_on: [phase2-validate-workflow]
acceptance_criteria:
  - "evals/replay.py exits non-zero on golden-run divergence"
  - ".github/workflows/eval.yml is a required check on PRs"
  - "At least one golden run in evals/golden/ exercises the full generate -> validate path"
```

---

## Phase 3 — Agentic features (post PR #1)

### LLM Interview runtime — wire prompts/interview.v1.md into a real stage

```yaml
id: llm-interview-runtime
title: "Phase 3: wire prompts/interview.v1.md into orchestrator/agentic_alz/stages/interview.py"
milestone: "Phase 3 — Agentic features"
labels: [area:orchestrator, area:llm, human-only]
agent_eligible: false
depends_on: [phase2-validate-workflow, llm-interview-stage]
acceptance_criteria:
  - "stages/interview.py exposes run_interview_offline + run_interview_live; live mode gates on assert_frontier and Budget"
  - "agentic-alz interview --transcript <jsonl> renders schema-valid inputs.yaml without an LLM call"
  - "Live mode (--live --model) is wired to a real provider client and honours LLM_TOKEN_BUDGET"
  - "evals/golden/interview-hns-minimal/ has a transcript whose terminal assistant turn round-trips to the existing hns-minimal inputs.yaml"
```

Stage-runtime code lives entirely in `orchestrator/`, but anything that
adds a provider client or bumps the v1 prompt is sensitive — kept
`human-only` until that lands. The offline transcript path is already
implemented in PR following the squad bootstrap; this item tracks the
remaining live-mode wiring.

### Lab mode bundle — fast sandbox bring-up

```yaml
id: lab-mode-bundle
title: "Phase 3: lab mode emits a self-contained sandbox bundle"
milestone: "Phase 3 — Agentic features"
labels: [area:orchestrator, area:operate]
agent_eligible: true
depends_on: [phase2-validate-workflow]
acceptance_criteria:
  - "agentic-alz lab init --inputs --out emits a tar.gz with rendered Terraform + lab-manifest.json"
  - "CLI refuses inputs whose tags.defaults.Environment != 'sandbox'"
  - "Bundle strips the production backend.tf so labs run on local state"
  - "docs/lab-mode.md documents the path including a red banner on local state"
  - "AGENTIC_ALZ_DISABLED short-circuits lab init"
```

Pure orchestrator + docs + golden fixture; no apply path, no LLM, no
sensitive-surface changes — eligible for the agent.

### MCP server allowlist

```yaml
id: mcp-allowlist
title: "Phase 3: docs/mcp.allowlist.yaml + agentic_alz.mcp.assert_allowed wrapper"
milestone: "Phase 3 — Agentic features"
labels: [area:orchestrator, area:security, human-only]
agent_eligible: false
depends_on: [phase2-validate-workflow]
acceptance_criteria:
  - "docs/mcp.allowlist.yaml lists each permitted MCP server with mode (read/write) and notes"
  - "agentic_alz.mcp.assert_allowed(server, tool, mode) refuses non-allowlisted servers and refuses mode='write' for any server in v1"
  - "OPA policy enforces no PR may add 'mode: write' without NetSec CODEOWNER approval"
  - "MCP-derived data is treated as untrusted: schema-validated and length-bounded before any downstream use"
```

New sensitive surface, parallel to `docs/models.allowlist.yaml`. Stays
human-driven for the same reasons.

### Typed RCG schema

```yaml
id: firewall-rcg-schema
title: "Phase 3: schemas/rcg.schema.json types Rule Collection Groups end-to-end"
milestone: "Phase 3 — Agentic features"
labels: [area:schemas, area:security, human-only]
agent_eligible: false
depends_on: [phase2-validate-workflow]
acceptance_criteria:
  - "schemas/rcg.schema.json validates network and application rule collections with priority + action"
  - "Wildcard FQDNs and wildcard destinations are rejected at schema level (defence in depth with policies/firewall_rules.rego)"
  - "Round-trip test: every firewall-policy/lib/<pattern>/rcg.json validates against the schema"
  - "Composer prompt and (future) firewall importer both produce documents that validate against this schema"
```

Schema lives under `schemas/` — `human-only` per the consensus plan.
The first-cut document is in this PR; further iteration tracked here.

### Firewall lib skeleton — concrete pre-approved RCGs

```yaml
id: firewall-lib-skeleton-example
title: "Phase 3: in-repo firewall-policy/lib/<pattern>/ exemplars"
milestone: "Phase 3 — Agentic features"
labels: [area:firewall, area:terraform]
agent_eligible: true
depends_on: [firewall-rcg-schema]
acceptance_criteria:
  - "Each lib pattern has main.tf + variables.tf + README.md + rcg.json"
  - "Every rcg.json validates against schemas/rcg.schema.json"
  - "policies/firewall_rules.rego passes against each main.tf"
  - "At least the patterns enumerated in firewall-policy/lib/README.md ship as exemplars"
```

In-repo only — does not touch the real `alz-firewall-policy` sibling
repo (which is created by the human-only `phase1-sibling-repos`).

### Firewall importer — read-only MCP -> typed RCG diff

```yaml
id: firewall-import-stage
title: "Phase 3: orchestrator stage imports live firewall state via Azure/ARM MCP (read-only)"
milestone: "Phase 3 — Agentic features"
labels: [area:orchestrator, area:firewall, area:security, human-only]
agent_eligible: false
depends_on: [mcp-allowlist, firewall-rcg-schema, phase1-sibling-repos]
acceptance_criteria:
  - "stages/firewall_import.py calls Azure MCP / ARM MCP read-only tools only (enforced by mcp.assert_allowed)"
  - "Output normalises to schemas/rcg.schema.json; raw Azure JSON is never pasted into Terraform"
  - "Diff against firewall-policy/lib/ HEAD is emitted as both markdown and machine-readable JSON"
  - "Nightly run files an issue (not a PR) on drift, symmetric to the platform drift detector"
  - "Composer-driven write path opens a PR against alz-firewall-policy and never pushes to main"
```

The full read-only importer + Composer write path. Stays `human-only`
for v1 — depends on the real sibling repo and on the new MCP allowlist.
