# Holden — History

**Project:** Agentic ALZ — deterministic GitOps pipeline for Azure Landing Zones (ALZ Accelerator + AVM + Terraform), with narrow LLM stages (Interview, Design, Drift Triage, Firewall Composer). Apply is never an LLM action.
**Stack:** Python 3 (orchestrator), Terraform/AVM (templates), OPA Rego (policies), GitHub Actions, MCP, frontier LLMs
**Repo:** martinopedal/agentic-alz
**Lead user:** martinopedal
**Cast at:** 2026-05-12T22:36:05Z

## Core Context

- AGENTS.md (root) is the canonical agent-instruction surface. `.github/copilot-instructions.md` is a 5-line stub pointing at it. `prompts/system/agent-preamble.v1.md` is the runtime mirror. All three carry matching `agent-instructions-version` markers. CI job `lint-instructions` enforces sync.
- Playbooks: `docs/playbooks/0X-*.md` — every non-trivial change picks one (or more) and must satisfy its `## Definition of Done`.
- Generated docs (`docs/generated/`) are auto-rendered by `scripts/gen_docs.py`. NEVER hand-edit. The `docs` workflow fails on any diff.
- Every PR must populate `## Rubberduck`, `## Multi-model judge`, `## Frontier-model attestation`, `## Playbook` sections. Bypass label: `incident`.

## Learnings

(append below — newest at top)

### 2026-05-13: Roadmap assignments — Phase 3 agentic features and synthesis

**Synthesis output:** 10-item prioritized agentic roadmap + 3 supporting infrastructure items. 5-member squad roster locked for v1 (Holden, Naomi, Amos, Bobbie, Alex). SRE agent rejected. Docs-always-updated endorsed.

**Assigned items (priority rank):**
4. Drift Triage (rank 4) - Day-2, fill skeleton with agentic triage

**Implementation spec:** Skeleton already exists at `stages/drift_triage.py`. Fill with: (1) read drift detection output (Azure Policy non-compliance, Terraform drift, firewall rule drift), (2) LLM triage + risk classification, (3) open advisory GitHub issue with remediation guidance. Routes through frontier-model allowlist, schema validation, kill-switch.

**Lifecycle position:** Runs post-apply as part of Day-2 monitoring. Never mutates Azure (read-only). Feeds into human triage and remediation workflow.

**Interdependency:** Independent. Can ship after Shared PR Opener (rank 7) is available for issue composition.

**Key architectural decisions finalized:**
- No SRE agent; SRE-shaped stages added incrementally (postmortem draft, compliance snapshot, patch triage)
- Docs-always-updated: two-tier (blocking PR gate + auto-regen safety net on main)
- Lifecycle map: Bootstrap (human) → Interview/Design (agentic-CLI) → Plan (det-CI + advisory) → Apply (det-CI, never agentic) → Day-2 (agentic-CI + CLI)
- Squad roster: Holden (Lead), Naomi, Amos, Bobbie, Alex. No changes for v1.
- AGENTS.md enhancement: Must add evals/replay.py and judge.py to "never edit" list (requires multi-model judge + separate PR)

**Shared insight:** Shared PR Opener (Naomi, rank 7) is the critical architectural enabler. Without it, each candidate rolls its own PR logic, fragmenting rubberduck/judge enforcement.
