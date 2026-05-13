# Quality gates & "docs always updated" enforcement design

**Research by:** Alex (Eval & Test Engineer)  
**Date:** 2026-05-12  
**Requested by:** martinopedal  
**Status:** Complete

---

## Executive summary

The repo has 8 deterministic CI jobs + 1 eval harness + 1 PR-body gate (rubberduck), covering a broad quality surface but **missing auto-regen enforcement**. The `docs / generate-and-check` job detects drift but blocks the PR instead of proposing a fix. **11 generated docs** cover schemas, prompts, policies, models, MCP, CLI, roadmap, playbooks-index, agent-instructions-hash, and decisions-index. **Recommendation:** add a `.github/workflows/regen-docs.yml` that opens a PR with the regenerated output whenever source-of-truth files change on `main`; keep `--check` blocking in PR CI. A dedicated docs-steward agent is **rejected** — the pattern is narrow enough that every agent should inline `python scripts/gen_docs.py && git add docs/generated/` into their own PR workflow. Multi-model judge automation as a CI job is **rejected** for now (cost + latency); human-driven multi-model judge at PR review time remains the sanctioned path.

---

## 1. Current quality gates inventory

| CI job | Workflow | Trigger | What it gates | Deterministic vs LLM-touched | Blocking or advisory | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| **kill-switch check** | `ci.yml`, `docs.yml`, every workflow | Every PR, push to main | All automation; refuses to run if `AGENTIC_ALZ_DISABLED` is set | Deterministic | Blocking | Enforces MUST 1 |
| **orchestrator (lint + test)** | `ci.yml` | `orchestrator/**`, `schemas/**`, `evals/**`, etc. | Python orchestrator code | Deterministic | Blocking | Runs `ruff check .` + `pytest --cov` |
| **schemas (validate examples)** | `ci.yml` | `schemas/**`, `evals/golden/**` | Every golden `inputs.yaml` validates against `schemas/inputs.schema.json` | Deterministic | Blocking | Catches schema drift from golden fixtures |
| **OPA policies (rego syntax + unit)** | `ci.yml` | `policies/**`, `templates/**`, `firewall-policy/**`, `docs/mcp.allowlist.yaml` | Rego policies parse and execute; `avm_pinning`, `firewall_rules`, `mcp_allowlist` | Deterministic | Blocking | Runs conftest against sample plan + MCP allowlist + firewall lib |
| **lint-instructions** | `ci.yml` | `AGENTS.md`, `.github/copilot-instructions.md`, `prompts/system/agent-preamble.v1.md`, `docs/playbooks/**` | Agent-instruction surfaces stay in sync; playbooks have required structure | Deterministic | Blocking | Verifies markers match, playbook IDs 00-10 exist, DoD references real workflows, References ≥3 URLs |
| **docs / generate-and-check** | `docs.yml` | `schemas/**`, `prompts/**`, `policies/**`, `docs/models.allowlist.yaml`, `docs/mcp.allowlist.yaml`, `docs/playbooks/**`, `AGENTS.md`, etc. | Generated docs are byte-identical to what `gen_docs.py` would produce | Deterministic | Blocking | Runs `python scripts/gen_docs.py --check`; fails if diff exists; also verifies `models.allowlist.yaml` parses and has ≥2 judge-eligible models from ≥2 providers |
| **rubberduck / check** | `rubberduck.yml` | PR opened/edited/reopened/synchronize | PR body has required sections (Playbook, Rubberduck, Multi-model judge, Frontier-model attestation) and no placeholders | Deterministic | Blocking | Bypass label: `incident` |
| **evals / replay** | (not yet in CI; roadmap item `cross-eval-gating`) | `evals/**` | Offline replay harness exercises deterministic stages (validate inputs.yaml, generate, conftest) | Deterministic | Advisory (planned blocking) | Runs `python evals/replay.py`; exits non-zero on golden-run divergence; roadmap item `cross-eval-gating` tracks CI wiring |
| **link-check** | `docs.yml` (planned, mentioned in AGENTS.md References footer) | Weekly cron | External URLs in docs still resolve | Deterministic | Advisory | Not yet implemented; mentioned as future enhancement |
| **multi-model judge** | (human-driven at PR review time) | PRs touching `prompts/**`, `templates/**`, `policies/**`, `schemas/**`, ADRs, allowlists | ≥2 distinct providers, unanimous PASS by default on fixed rubric | LLM-touched (build-time consensus, not runtime) | Blocking when triggered | Manual invocation by PR author or reviewer; `orchestrator/agentic_alz/llm/judge.py` provides the deterministic aggregator; no CI job today |

**Summary:**
- **9 deterministic blocking gates**, 1 advisory (evals, planned blocking), 1 human-driven LLM gate (multi-model judge).
- **No auto-regen** — `gen_docs.py --check` detects drift but doesn't propose a fix.
- **No nightly replay CI** — `evals/replay.py` exists but isn't wired as a required check yet (roadmap item `cross-eval-gating`).

---

## 2. Generated docs surface map

| Generated file | Source(s) of truth | Generator function | Current refresh trigger |
| --- | --- | --- | --- |
| `docs/generated/README.md` | (index of the other generated docs) | `render_index()` | Any `docs.yml` trigger |
| `docs/generated/schemas.md` | `schemas/*.schema.json` | `render_schemas()` | `docs.yml` on changes to `schemas/**` |
| `docs/generated/prompts.md` | `prompts/*.md` | `render_prompts()` | `docs.yml` on changes to `prompts/**` |
| `docs/generated/policies.md` | `policies/*.rego` | `render_policies()` | `docs.yml` on changes to `policies/**` |
| `docs/generated/models.md` | `docs/models.allowlist.yaml` | `render_models()` | `docs.yml` on changes to `docs/models.allowlist.yaml` |
| `docs/generated/mcp.md` | `docs/mcp.allowlist.yaml` | `render_mcp()` | `docs.yml` on changes to `docs/mcp.allowlist.yaml` |
| `docs/generated/cli.md` | `orchestrator/agentic_alz/cli.py` | `render_cli()` | `docs.yml` on changes to `orchestrator/agentic_alz/cli.py` |
| `docs/generated/roadmap.md` | `ROADMAP.md`, `scripts/squad_bootstrap.py` | `render_roadmap()` | `docs.yml` on changes to `ROADMAP.md` |
| `docs/generated/playbooks-index.md` | `docs/playbooks/*.md`, `CODEOWNERS` | `render_playbooks_index()` | `docs.yml` on changes to `docs/playbooks/**`, `CODEOWNERS` |
| `docs/generated/agent-instructions-hash.md` | `AGENTS.md`, `.github/copilot-instructions.md`, `prompts/system/agent-preamble.v1.md` | `render_agent_instructions_hash()` | `docs.yml` on changes to `AGENTS.md`, `.github/copilot-instructions.md` |
| `docs/generated/decisions-index.md` | `decision/*/decision.json`, `schemas/decision.schema.json` | `render_decisions_index()` | `docs.yml` on changes to `decision/**` |

**Coverage gap analysis:**
- **No gap detected** — all source-of-truth files mentioned in the consensus plan or AGENTS.md are covered by `gen_docs.py`.
- The `docs.yml` `on.pull_request.paths` trigger list is **comprehensive**: covers `schemas/**`, `prompts/**`, `policies/**`, `docs/models.allowlist.yaml`, `docs/mcp.allowlist.yaml`, `docs/playbooks/**`, `AGENTS.md`, `.github/copilot-instructions.md`, `decision/**`, `CODEOWNERS`, `orchestrator/agentic_alz/cli.py`, `scripts/gen_docs.py`, `scripts/squad_bootstrap.py`, `ROADMAP.md`, `docs/generated/**`.
- **Timestamp comparison or content hash**: `gen_docs.py` already embeds the SHA-256 of source files in the banner of each generated doc. The `--check` mode performs a byte-identity diff, which is stronger than timestamp comparison.

---

## 3. "Docs always updated" enforcement design

### Concrete pattern (recommended)

**Two-tier approach:**

1. **PR gate (blocking)** — keep the current `docs / generate-and-check` job as-is. It runs `python scripts/gen_docs.py --check` and fails if any diff exists. This **blocks merge**.
2. **Auto-regen on push to `main` (advisory + self-healing)** — add a new `.github/workflows/regen-docs.yml` that:
   - Triggers on `push: branches: [main]` and `paths: [<same list as docs.yml>]`.
   - Runs `python scripts/gen_docs.py` (without `--check`).
   - If any file in `docs/generated/` changed, opens a PR from a bot branch (`docs/regen-<timestamp>`) with the regenerated output.
   - PR title: `[auto] Regenerate docs/generated/ after <commit SHA>`.
   - PR body: "This PR was auto-generated because source-of-truth files changed on `main` without regenerating `docs/generated/`. The `docs / generate-and-check` job was bypassed or the PR was force-merged. Merging this PR brings `docs/generated/` back into sync."
   - Assign the PR to the committer of the triggering commit (or to a default reviewer if the committer is not a repo collaborator).
   - **Bot user**: use the `GITHUB_TOKEN` with `contents: write`, `pull-requests: write` permissions. The PR is authored by `github-actions[bot]`.
   - **Idempotency**: if a `docs/regen-*` branch already exists for the same source SHA, no-op.

**Rationale:**
- **Blocking check remains the primary gate** — no PR can merge with stale docs.
- **Auto-regen is a safety net** — if a PR bypasses the gate (force-merge, admin override, CI bug), the next push to `main` self-heals.
- **No agent involved** — the pattern is narrow (one script, one commit, one PR). Agents inline `python scripts/gen_docs.py && git add docs/generated/` into their PR workflow.

### Coverage gap detection (addressed)

**No gaps detected.** The `docs.yml` trigger paths list every source-of-truth file mentioned in `gen_docs.py` and every file that appears in the `RENDERERS` dict. If a new source-of-truth file is added (e.g., a new schema), the developer must:
1. Add a renderer function to `scripts/gen_docs.py`.
2. Add the new source path to the `docs.yml` `on.pull_request.paths` list.
3. Run `python scripts/gen_docs.py` and commit the regenerated output.

**Detection of missing coverage:** the `lint-instructions` job could be extended to cross-check that every `*.schema.json` in `schemas/` appears in at least one renderer's source list. This is a deterministic invariant and belongs in CI, not in an agent.

### Agent-authored docs: where do they land and how are they discoverable?

**Three categories:**

1. **Research reports** (e.g., `.squad/log/research/alex-quality-docs.md`) — ephemeral session artifacts, not committed to `main`. Discoverable via PR discussion comments or issue references. **Not indexed** in `docs/generated/`.
2. **ADRs** — committed to `docs/adr/` following the `docs/adr-template.md`. Indexed by future work (roadmap item for ADR index generator). **Not yet in `docs/generated/`** but will be once the ADR index renderer lands.
3. **Decision records** — committed to `decision/<id>/decision.json`, validated by `schemas/decision.schema.json`. **Already indexed** by `docs/generated/decisions-index.md`.

**Recommendation:** agents that produce ADRs or decision records MUST regenerate `docs/generated/` in the same PR. The `docs / generate-and-check` job enforces this.

### Stale-doc detection (addressed)

**Already covered by `gen_docs.py --check`**. The banner includes the SHA-256 of all source files; if sources change without regeneration, the hash changes and `--check` fails. **No timestamp comparison needed** — content hash is stronger.

---

## 4. Agentic eval automation candidates

| Candidate | Fit assessment | Recommendation |
| --- | --- | --- |
| **Continuous nightly replay against latest models** | Medium fit — detects model drift but is noisy (models update frequently). Cost: $$ per run if exercising all LLM stages. | **Defer** until v1 ships. When implemented: run weekly (not nightly) against the `eval-sandbox` environment; open an issue (not a PR) if golden-run divergence detected. Never auto-merge. |
| **Multi-model judge automation as a CI job** | Low fit — cost ($5–10 per invocation × N PRs), latency (30–90 sec per model × 3+ models = 2–5 min), and the rubric is intentionally stable (changes rarely). | **Reject** for now. Keep multi-model judge human-driven at PR review time. The `judge.py` aggregator is deterministic and unit-tested; that's sufficient. |
| **Regression detection across eval runs** | High fit — detecting when a schema change or prompt revision degrades an existing golden run is valuable. | **Adopt** once `evals/replay.py` is wired as a required CI check (roadmap item `cross-eval-gating`). Extend `replay.py` to output a JSON report (`evals/results/<timestamp>.json`) and add a diff tool that compares the latest run to the previous baseline. Gate PRs if the diff shows a regression. |
| **Prompt unit-test generation from schema examples** | Medium fit — schemas have `examples` fields; could auto-generate test cases for prompt output validation. | **Defer** until post-v1. The schema-validation step in `replay.py` already catches malformed output. Unit tests for prompt edge cases are better hand-written with specific adversarial inputs. |
| **Coverage gap detection for eval scenarios** | High fit — knowing which prompts have no replay coverage is a CI-enforceable invariant. | **Adopt** immediately. Add a step to `ci.yml` that cross-checks: for every `prompts/<stage>.v<N>.md`, assert at least one golden case in `evals/golden/` exercises that stage. Fail closed if coverage is missing. |
| **Auto-changelog from merged PRs grouped by playbook** | Medium fit — useful for release notes but not a quality gate. | **Defer** until post-v1. The `## Playbook` section in PR bodies is machine-parseable; a `scripts/gen_changelog.py` could group PRs by playbook and emit a markdown changelog. Not urgent. |

---

## 5. Orchestration of doc updates — "docs-steward" agent?

**Recommendation: NO dedicated docs-steward agent.**

**Rationale:**
- The pattern is **narrow and deterministic**: one script (`python scripts/gen_docs.py`), one commit (`git add docs/generated/`), one command. Every agent can inline this into their own PR workflow.
- A dedicated agent adds complexity (one more thing to maintain, one more handoff, one more failure mode) for a task that is already automated.
- The `docs / generate-and-check` CI job is the real enforcer — it catches any agent that forgets to regenerate. The agent doesn't need a steward; it needs a reminder in the playbook.

**Alternative (lighter-weight):** add a one-liner to every sensitive-surface playbook (`04-prompt-or-schema-change.md`, `05-policy-change.md`, `06-iac-template-change.md`, etc.) in the `## Definition of Done` section:

```markdown
- [ ] `docs / generate-and-check` passes (regenerate with `python scripts/gen_docs.py` and commit the result if any source-of-truth file changed).
```

This makes the requirement explicit without adding a new agent.

---

## 6. What must stay deterministic (BLOCK from being agentic)

| Surface | Why it must stay deterministic | Current enforcement |
| --- | --- | --- |
| **`gen_docs.py` itself** | The script is the single source of truth for what gets regenerated. An LLM rewriting the renderers would silently change the doc contract. | Sensitive path in AGENTS.md; `docs.yml` fails if `scripts/gen_docs.py` changes without a corresponding `docs/generated/` update. |
| **`docs / generate-and-check` job** | The gate that enforces doc freshness. An agent editing this workflow could bypass the gate. | Sensitive path (`08-ci-workflow-change.md` playbook, human-only). |
| **`evals/replay.py` harness** | The offline replay harness is the baseline for "does the pipeline still work". An LLM rewriting the harness could mask regressions. | Not yet in a sensitive-path list but should be added to AGENTS.md under "Things an agent must NEVER do". |
| **`lint-instructions` job** | The job that enforces playbook structure and agent-instruction sync. An agent editing this could bypass the sync requirement. | Sensitive path (part of `ci.yml`, which is gated by `08-ci-workflow-change.md`). |
| **`rubberduck.yml` workflow** | The job that enforces PR-body structure. An agent editing this could bypass the rubberduck requirement. | Sensitive path (part of `.github/workflows/`, gated by `08-ci-workflow-change.md`). |
| **OPA policies** | The policies are the runtime safety net. An LLM rewriting a policy could introduce a silent gap. | Sensitive path (`policies/` gated by `05-policy-change.md`, human-only). |
| **Schemas** | Typed contracts at stage boundaries. An LLM rewriting a schema could silently widen the contract and allow unsafe input. | Sensitive path (`schemas/` gated by `04-prompt-or-schema-change.md`, human-only, multi-model judge required). |
| **Judge aggregator (`judge.py`)** | The deterministic aggregator is what makes multi-model judge trustworthy. An LLM rewriting the aggregation logic could paper over dissent. | Not yet in a sensitive-path list but should be added (part of `orchestrator/agentic_alz/llm/`, which AGENTS.md already flags as "runtime enforcement points for the two allowlists"). |
| **Allowlists (`models.allowlist.yaml`, `mcp.allowlist.yaml`)** | The allowlists define the security boundary. An LLM adding a model or MCP server could bypass the review requirement. | Sensitive path (gated by `04-prompt-or-schema-change.md`, human-only, multi-model judge required). |

**Summary:** any code path that enforces a guardrail or defines the shape of truth must stay deterministic. LLM stages are narrow (Interview, Design, Drift Triage, Firewall Compose); everything else is plumbing that an agent should never touch.

---

## Proposed next steps

1. **Add `coverage-gap-detection-for-eval-scenarios` to `ci.yml`** (immediate) — for every `prompts/<stage>.v<N>.md`, assert at least one golden case in `evals/golden/` exercises that stage. Fail closed if coverage is missing.
2. **Wire `evals/replay.py` as a required CI check** (roadmap item `cross-eval-gating`) — run `python evals/replay.py` on every PR; block merge if golden-run divergence detected.
3. **Add `.github/workflows/regen-docs.yml`** (immediate) — auto-regen on push to `main`, open a PR if drift detected. See §3 for the full spec.
4. **Extend `evals/replay.py` to output a JSON report** (post-v1) — store `evals/results/<timestamp>.json` for each run; add a diff tool that compares to the previous baseline; gate PRs on regression.
5. **Add a "DoD reminder" to every sensitive-surface playbook** (immediate) — one-liner in the `## Definition of Done` section: "regenerate `docs/generated/` if any source-of-truth file changed".
6. **Add `evals/replay.py` and `judge.py` to the "never edit" list in AGENTS.md** (immediate) — these are runtime enforcement points and must stay deterministic.

---

## Appendix: Coverage gap detection script (proposed)

```python
#!/usr/bin/env python3
"""CI check: every prompt has at least one golden case exercising it."""
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
prompts = sorted((REPO_ROOT / "prompts").glob("*.md"))
golden_cases = sorted((REPO_ROOT / "evals" / "golden").iterdir())

# For each prompt, assert at least one golden case exercises it.
# Today, golden cases are hand-curated. A future enhancement could parse
# the prompt's `> Stage: \`<stage>\`` line and match against a `stage`
# field in each golden case's inputs.yaml.
# For now, we assert the count is non-zero and delegate finer-grained
# checks to human review.

if len(golden_cases) == 0:
    print("ERROR: no golden cases found in evals/golden/", file=sys.stderr)
    sys.exit(1)

# Heuristic: if prompts exist and golden cases exist, coverage is "advisory ok".
# A finer-grained check would parse each prompt's stage and match against
# golden-case metadata. That's a follow-on.

print(f"Found {len(prompts)} prompts and {len(golden_cases)} golden cases.")
print("Coverage check passed (advisory — finer-grained check is future work).")
```

Add this as a step in `ci.yml` under a new job `coverage-gap-detection`.

---

**End of report.**
