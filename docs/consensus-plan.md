# Agentic ALZ — Consensus Plan (v1)

This is the implemented plan. It was synthesised from critique by three
frontier models (GPT-5.5, Claude Opus 4.6, Gemini 2.5 Pro) and is the source
of truth for what v1 ships.

## 0. Reframing

Agentic ALZ is a **deterministic GitOps pipeline orchestrator** with a small
number of **narrow LLM-powered stages**, not a swarm of autonomous agents.
LLMs are used for interview Q&A, ADR drafting, drift triage and rule-collection
synthesis. They are kept *out* of destructive paths. **Apply is a CI job, not
an LLM action.**

## 1. Vision and non-goals

**Vision.** Let a CSA bring up an Azure Landing Zone (ALZ Accelerator + AVM +
Terraform) by answering an interview, then operate it via a PR-driven workflow
with agentic assistance for design, drift triage, cost reasoning and firewall
change requests.

**Non-goals for v1.**

- No autonomous apply. Every apply is human-approved through a protected
  GitHub Environment.
- No multi-tenant orchestration.
- No subscription vending agent (vending exists, but is invoked by a
  deterministic onboarding workflow, not an LLM).
- No Sentinel content generation.
- No multi-model "consensus" loop at runtime.
- No auto-remediation of drift; drift opens issues/PRs only.

## 2. Repository topology

- `agentic-alz/` — this repo: orchestrator, prompts, schemas, golden inputs,
  eval harness, OPA policies, CI.
- `alz-platform/` — generated platform Terraform (split from orchestrator so
  the agent code can iterate without touching infra state).
- `alz-firewall-policy/` — separate repo, separate Terraform state, NetSec
  CODEOWNER. Holds:
  - `policies/base/` — baseline RCGs deployed at bootstrap.
  - `lib/` — versioned, pre-approved Rule Collection Groups workloads consume
    by reference.
- `alz-workloads/<name>/` — per-workload, per-state, AVM-based.

State backend: Azure Storage in the **management subscription**, one container
per repo, blob-lease locking, CMK, private endpoint, soft-delete + versioning,
RBAC-only, no shared keys. Cross-state coupling is via published interface
artifacts (typed JSON in versioned blobs), not by reading remote state across
repos.

## 3. Pre-work (de-risk)

1. **Hand-build a golden ALZ.** See `templates/hub-and-spoke/`. Two reference
   shapes are planned: hub-and-spoke + Azure Firewall Premium (v1) and vWAN
   secured hub (v1.1).
2. **Lock the AVM allowlist.** See `templates/hub-and-spoke/versions.lock`.
   Approved module sources and exact versions are captured here. `ref=main` is
   forbidden by [`policies/avm_pinning.rego`](../policies/avm_pinning.rego).
3. **Inventory eventual-consistency landmines.** See
   [`eventual-consistency.md`](eventual-consistency.md).

## 4. Architecture

A LangGraph-based orchestrator drives a typed state machine. Nodes are either
**deterministic** (TF, lint, scan, plan, infracost, policy whatif, GitHub ops)
or **LLM stages** with strict input/output JSON schemas. Every transition is
checkpointed.

### Pipeline (v1)

1. **Interview** (LLM) — minimal schema only. Output: `inputs.yaml` validated
   by `schemas/inputs.schema.json`. Hand-edit is a first-class path.
2. **Design** (LLM) — produces ADR + decision rules. Output is a typed
   `design.json` (`schemas/design.schema.json`).
3. **Generate** (deterministic + templated) — emits Terraform from
   `design.json` against the golden templates and the AVM allowlist.
4. **Validate** (parallel deterministic jobs) — `terraform fmt/validate`,
   `tflint`, `checkov`, `terraform plan`, `infracost diff`, ARM what-if for
   policy assignments only, OPA conformance.
5. **Risk classification** (deterministic) — typed risk report
   (`schemas/risk.schema.json`).
6. **Human approval** — PR review + protected GitHub Environment.
7. **Deploy** (deterministic CI job) — applies the immutable saved plan
   artifact, never a regenerated plan; re-runs `terraform plan` post-apply.
8. **Post-deploy verification** — polls Azure to confirm key resources exist.

### LLM stages only at these nodes

Interview, Design (ADR), Drift Triage, Firewall Change Composer.

## 5. Identity, permissions, blast radius

Per-phase Entra ID workload identities, all OIDC-federated to GitHub, no PATs:
`alz-readonly`, `alz-plan`, `alz-apply-platform`, `alz-apply-firewall`,
`alz-vending`. Break-glass accounts are separate, hardware-key MFA, monitored,
never used by automation. See [`threat-model.md`](threat-model.md).

Hard rules:

- Apply jobs run only in the protected `prod` GitHub Environment.
- `terraform destroy` blocked by CI policy by default.
- Destructive-op deny-list at the wrapper script level.
- Global **kill switch** (`AGENTIC_ALZ_DISABLED` repo variable) halts all
  scheduled and triggered orchestrator runs.

## 6. MCP server roles

| Server | Role |
| --- | --- |
| azure-mcp | Read inventory, RBAC reads, post-deploy polling. Never mutates. |
| arm-mcp | What-if for ARM/Bicep and policy assignments only. |
| terraform-mcp | AVM module discovery and version resolution. Never invoked at apply time. |
| microsoft-learn-mcp | Advisory only, used by Design for citations. |
| github-mcp | PRs, issues, checks, environment approvals. |
| infracost | CLI in CI, not MCP. |

## 7. Firewall repo model

Federated library model. Workload repos compose RCGs from `lib/` by reference.
The Firewall Change Composer LLM stage proposes **PRs** against `lib/`; NetSec
reviews. The agent never pushes to `main`.

## 8. Bootstrap

Three phases — see [`phase-0-prerequisites.md`](phase-0-prerequisites.md) and
[`bootstrap/phase1.sh`](../bootstrap/phase1.sh). Phase 2 is the pipeline
deploying itself.

## 9. Day-2 operate mode (read-mostly)

Nightly drift detection (with post-apply 2-hour cooldown), weekly cost report,
policy compliance scan, RBAC drift detector. All open issues; none auto-merge.

## 10. Safety, observability, eval

Per-stage LLM token budget, per-tool timeout (30 min on `terraform apply`),
structured logs (trace ID, input hash, output hash, tool calls, identity,
commit SHA), OpenTelemetry traces, replayable runbook (every stage produces a
checkpoint blob), eval harness (golden runs gate CI). See
[`runbook.md`](runbook.md) and [`incident-response.md`](incident-response.md).

## 11. MVP scope

In scope (v1): greenfield ALZ deploy for hub-and-spoke + Azure Firewall
Premium end-to-end through the pipeline; firewall repo with base RCGs and
initial `lib/`; read-only Day-2; eval harness with at least one golden run
gating CI; kill switch, OIDC identities, protected environments, blast-radius
gate, replay checkpoints.

Deferred: vWAN topology, drift remediation PRs, firewall change composer,
onboarding/subscription vending, Sentinel content, multi-tenant, multi-model
judge.

## 12. Repo layout

See [`README.md`](../README.md).
