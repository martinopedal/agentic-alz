# Alex — History

**Project:** Agentic ALZ — deterministic GitOps pipeline for Azure Landing Zones (ALZ Accelerator + AVM + Terraform), with narrow LLM stages (Interview, Design, Drift Triage, Firewall Composer). Apply is never an LLM action.
**Stack:** Python 3 (orchestrator), Terraform/AVM (templates), OPA Rego (policies), GitHub Actions, MCP, frontier LLMs
**Repo:** martinopedal/agentic-alz
**Lead user:** martinopedal
**Cast at:** 2026-05-12T22:36:05Z

## Core Context

- Verified baseline: `cd orchestrator && pip install -e '.[dev]' && pytest && ruff check .`
- Replay harness: `python evals/replay.py`. Generated docs drift: `python scripts/gen_docs.py --check`.
- `lint-instructions` CI job enforces AGENTS.md ↔ `.github/copilot-instructions.md` ↔ `prompts/system/agent-preamble.v1.md` sync.
- Playbook tests: `orchestrator/tests/test_playbooks.py` validates each `docs/playbooks/0X-*.md` has Triggers, Definition of Done (referencing real workflow stems via `<workflow> / <job>`), and References (≥3 URLs).

## Learnings

(append below — newest at top)

### 2026-05-13: Roadmap assignments — Phase 3 agentic features

**Assigned items (priority rank):**
2. Rubberduck Generator (rank 2) - Plan stage (PR), auto-populate template sections
6. ALZ Conformance Explainer (rank 6) - Plan stage, OPA denial → CAF docs mapping

**Implementation order:** Rubberduck Generator (immediate, PR friction reduction), ALZ Conformance Explainer (educational value, advisory-only).

**Pattern to establish:** Both items follow existing playbook patterns. Rubberduck is PR-side automation (on PR open, LLM reads diff + playbook metadata). Conformance is feedback loop on OPA denials (when conftest fails, LLM explains why + remediation links).

**Infrastructure ownership:** Alex also owns coverage-gap-detection CI job (cross-checks prompts ↔ golden cases) and regen-docs.yml (safety net for docs drift on main). Both support the docs-always-updated directive.

**Interdependency:** Rubberduck depends on Shared PR Opener (Naomi, rank 7). Conformance is independent.

### 2026-05-12: Quality gates & docs-always-updated enforcement

**Current gate map:**
- 9 deterministic blocking CI jobs: kill-switch, orchestrator lint+test, schema validation, OPA policies (rego+unit), lint-instructions, docs/generate-and-check, rubberduck
- 1 advisory gate (evals/replay.py, not yet wired as required check — roadmap item `cross-eval-gating`)
- 1 human-driven LLM gate (multi-model judge at PR review time, not CI)
- **Gap:** no auto-regen on push to `main`; `gen_docs.py --check` blocks PRs but doesn't self-heal force-merge/admin-override scenarios

**Generated docs coverage map (11 files):**
- `docs/generated/schemas.md` ← `schemas/*.schema.json`
- `docs/generated/prompts.md` ← `prompts/*.md`
- `docs/generated/policies.md` ← `policies/*.rego`
- `docs/generated/models.md` ← `docs/models.allowlist.yaml`
- `docs/generated/mcp.md` ← `docs/mcp.allowlist.yaml`
- `docs/generated/cli.md` ← `orchestrator/agentic_alz/cli.py`
- `docs/generated/roadmap.md` ← `ROADMAP.md` + `scripts/squad_bootstrap.py`
- `docs/generated/playbooks-index.md` ← `docs/playbooks/*.md` + `CODEOWNERS`
- `docs/generated/agent-instructions-hash.md` ← `AGENTS.md` + `.github/copilot-instructions.md` + `prompts/system/agent-preamble.v1.md`
- `docs/generated/decisions-index.md` ← `decision/*/decision.json` + `schemas/decision.schema.json`
- `docs/generated/README.md` ← (index of the above)
- **No coverage gaps** — all source-of-truth files mentioned in AGENTS.md or consensus plan are covered by `gen_docs.py`

**"Docs always updated" pattern (two-tier):**
1. **PR gate (blocking, existing):** `docs / generate-and-check` runs `python scripts/gen_docs.py --check`; blocks merge if diff exists. **Enhancement:** add one-liner to every sensitive-surface playbook DoD: "regenerate docs if source-of-truth changed."
2. **Auto-regen on push to `main` (advisory, proposed):** new `.github/workflows/regen-docs.yml` opens a PR with regenerated output if drift slips through (force-merge, admin override, CI bug). Bot-authored PR, requires human review, never auto-merges.
3. **Agent inline responsibility:** no dedicated docs-steward agent; every agent that touches a source-of-truth file regenerates `docs/generated/` in the same PR. The CI gate enforces this.

**What must stay deterministic:**
- `scripts/gen_docs.py` itself (the script is the contract)
- `.github/workflows/docs.yml` (the gate that enforces freshness)
- `evals/replay.py` (the baseline for "does the pipeline still work")
- `orchestrator/agentic_alz/llm/judge.py` (the deterministic aggregator for multi-model consensus)
- OPA policies, schemas, allowlists (runtime enforcement points)

**Agentic eval automation (recommendations):**
- **Adopt immediately:** coverage-gap-detection (for every prompt, assert ≥1 golden case exercises it; fail closed if missing)
- **Adopt once `cross-eval-gating` ships:** regression detection across eval runs (store `evals/results/<timestamp>.json` per run; diff against baseline; gate PRs on regression)
- **Defer until post-v1:** nightly model-drift detection (run weekly, open issue not PR, never auto-merge), prompt unit-test generation from schema examples, auto-changelog from PRs grouped by playbook
- **Reject for now:** multi-model judge as CI job (cost $5–10 per invocation, latency 2–5 min, rubric changes rarely; keep human-driven at PR review time)
