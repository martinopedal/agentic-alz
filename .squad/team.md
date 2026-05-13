# Team

**Project:** Agentic ALZ — deterministic GitOps pipeline for Azure Landing Zones
**Stack:** Python 3 (orchestrator), Terraform/AVM (templates), OPA Rego (policies), GitHub Actions, MCP, frontier LLMs
**Repo:** martinopedal/agentic-alz
**Lead user:** martinopedal
**Cast at:** 2026-05-12T22:36:05Z
**Cast universe:** The Expanse (easter egg — never explain in user-facing output)

## Project Context

Agentic ALZ is a deterministic GitOps pipeline that helps a Cloud Solution Architect bring up and operate an Azure Landing Zone (ALZ Accelerator + Azure Verified Modules + Terraform), with **narrow LLM-powered stages** (Interview, Design, Drift Triage, Firewall Composer). Apply is **never** an LLM action — it is a CI job consuming an immutable saved plan artifact in a protected GitHub Environment.

The five hard guardrails (see `AGENTS.md`):

1. Kill switch (`AGENTIC_ALZ_DISABLED`)
2. Frontier-model allowlist (`docs/models.allowlist.yaml`)
3. MCP server allowlist (`docs/mcp.allowlist.yaml`)
4. AVM pinning (`policies/avm_pinning.rego`)
5. Rubberduck PR gate (`.github/workflows/rubberduck.yml`)

`AGENTS.md` (root) is the canonical agent-instruction surface; squad decisions extend it but never override.

## Members

| Name   | Role                  | Folder              | Badge        |
|--------|-----------------------|---------------------|--------------|
| Holden | Lead                  | `agents/holden/`    | 🏗️ Lead      |
| Naomi  | Python Engineer       | `agents/naomi/`     | 🔧 Backend   |
| Amos   | Platform Engineer     | `agents/amos/`      | ⚙️ Platform  |
| Bobbie | Security Engineer     | `agents/bobbie/`    | 🔒 Security  |
| Alex   | Eval & Test Engineer  | `agents/alex/`      | 🧪 Test      |
| Scribe | Session Logger        | `agents/scribe/`    | 📋 Scribe    |
| Ralph  | Work Monitor          | `agents/ralph/`     | 🔄 Monitor   |
