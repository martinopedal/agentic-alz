# Naomi — History

**Project:** Agentic ALZ — deterministic GitOps pipeline for Azure Landing Zones (ALZ Accelerator + AVM + Terraform), with narrow LLM stages (Interview, Design, Drift Triage, Firewall Composer). Apply is never an LLM action.
**Stack:** Python 3 (orchestrator), Terraform/AVM (templates), OPA Rego (policies), GitHub Actions, MCP, frontier LLMs
**Repo:** martinopedal/agentic-alz
**Lead user:** martinopedal
**Cast at:** 2026-05-12T22:36:05Z

## Core Context

- Orchestrator lives in `orchestrator/agentic_alz/`. Verified baseline: `cd orchestrator && pip install -e '.[dev]' && pytest && ruff check .`
- LLM router: `orchestrator/agentic_alz/llm/models.py` exposes `assert_frontier(model_id, role=...)` against `docs/models.allowlist.yaml`.
- MCP runtime check: `orchestrator/agentic_alz/mcp/__init__.py` exposes `assert_allowed(server, tool, mode)` against `docs/mcp.allowlist.yaml`.
- Killswitch: `agentic_alz/killswitch.py` reads `AGENTIC_ALZ_DISABLED`.
- Terraform wrapper: `agentic_alz/terraform/wrapper.py`.
- Replay harness: `python evals/replay.py`. Generated docs check: `python scripts/gen_docs.py --check`.

## Learnings

(append below — newest at top)

### 2026-05-13: Roadmap assignments — Phase 3 agentic features

**Assigned items (priority rank):**
7. Shared PR Opener (rank 7) - Cross-cut, reusable advisory-PR primitive

**Implementation spec:** Extract `orchestrator/agentic_alz/github/pr.py` module exposing `open_advisory_pr(title, body, diff, judge_attestation, rubberduck_prefill)`. Routes through github-mcp PR/issue surface only. Pre-fills ## Rubberduck, ## Multi-model judge, ## Playbook sections on every opened PR.

**Impact:** Critical architectural enabler. Without it, Plan Summarizer, Rubberduck Generator, AVM Version-Bump, Drift Triage each roll their own PR logic, fragmenting enforcement and complicating execution.

**Implementation priority:** Ship Shared PR Opener as a separate PR *before* Plan Summarizer. All downstream items depend on this primitive.

**Interdependency:** Unblocks ranks 1, 2, 3, 4, 9. Naomi owns this as a cross-cutting capability.
