# Naomi — Orchestrator Surface Inventory (salvaged)

> **⚠️ SALVAGE NOTE:** Naomi (claude-sonnet-4.5) completed all research reads
> (~57 tool calls) but hit a tool-invocation degeneration before she could write
> this file herself. The Coordinator transcribed the bullet-level findings from
> her final response so Holden's synthesis has all four inputs. **Bullet-level
> fidelity only — none of Naomi's deeper reasoning per candidate is captured
> here.** Re-spawn Naomi as a standalone follow-up if depth-of-analysis is
> needed for any candidate before promoting it to ROADMAP.md.

## 1. Current Surface Map

### LLM stages (per `docs/consensus-plan.md`)

| Stage | State | Notes |
|---|---|---|
| Interview | **Partial** | Offline mode works; live mode stubbed |
| Design | **Unimplemented** | Schema present, no live wiring |
| Drift Triage | **Unimplemented** | Schema present, no live wiring |
| Firewall Composer | **Unimplemented** | Schema present, no live wiring |

### Deterministic stages (no LLM)

| Stage | State |
|---|---|
| Generate | Complete |
| Risk | Complete |

(Per-stage file paths, schemas, model wiring, and MCP touchpoints were read
but not transcribed. Re-spawn Naomi for a full per-stage breakdown if needed.)

## 2. Scaffolding Inventory (12 reusable primitives)

| # | Primitive | Purpose |
|---|---|---|
| 1 | `killswitch` | `AGENTIC_ALZ_DISABLED` env/var refusal |
| 2 | `budget` | Cost / token budget tracking |
| 3 | `checkpoint` | Stage resume / replay artifact |
| 4 | LLM allowlist | `assert_frontier(model_id, role=...)` |
| 5 | MCP allowlist | `assert_allowed(server, tool, mode)` |
| 6 | `judge` | Multi-model consensus aggregation |
| 7 | `guard` | (Likely cross-cutting validation; see source) |
| 8 | Schema validation | Typed contracts at stage boundaries |
| 9 | Logging | Structured run log |
| 10 | Hashing | Plan/artifact content addressing |
| 11 | Terraform wrapper | Subprocess control around `terraform` |
| 12 | Drift cooldown | Rate-limit drift triage |

Naomi's verbatim assessment: **"Excellent scaffolding"** — adding a new
narrow LLM stage is mostly composition of these 12 primitives.

## 3. New Stage Candidates (8)

| Name | Complexity | One-line scope (per Naomi) |
|---|---|---|
| Cost Advisor | **S** | Read plan output; advisory-only cost commentary |
| Template Optimizer | **S** | AVM/template diff suggestions; advisory PR comment |
| Documentation Generator | **M** | Auto-generate per-template README from inputs/outputs |
| RBAC Recommender | **M** | Least-privilege RBAC proposals from template intent |
| Compliance Mapper | **M** | Map template resources to ASB/CIS/ISO controls |
| Capacity Planner | **L** | Telemetry-driven right-sizing proposals |
| Security Posture Review | **L** | Cross-cutting security review on plan output |
| Runbook Generator | **L** | Generate operations runbook from architecture diff |

(Per-candidate input/output contracts, file paths, and guardrails were
identified by Naomi but not transcribed — re-spawn for detail.)

## 4. CLI vs Pipeline Split

Not transcribed at the per-candidate level. Naomi's general principle
(inferred): all candidates should be **callable from CLI for lab/dev** and
**runnable from pipeline for prod evidence**, with the deterministic
boundary unchanged. Re-spawn for per-candidate CLI/pipeline recommendation.

## 5. Infrastructure Gaps (M/L candidates need new shared primitives)

1. **Shared PR opener primitive** — most M/L candidates produce advisory PRs;
   today there is no shared abstraction for "open advisory PR with diff,
   judge attestation, and rubberduck section pre-filled". Recommend
   centralising in `orchestrator/agentic_alz/github/pr.py` (new module).
2. **Evidence collector** — Compliance Mapper, Security Posture Review, and
   Runbook Generator all need to bundle input + output + judge votes into
   a single evidence artifact. Recommend `orchestrator/agentic_alz/evidence/`.
3. **Cost tracking extension** — existing `budget` primitive tracks
   tokens/dollars per run; Cost Advisor and Capacity Planner need
   azure-resource-cost ingestion (Cost Management API). Recommend extending
   `budget` with a pluggable cost source interface.

## Headline takeaway (Coordinator-paraphrased from Naomi's final response)

> Scaffolding is in great shape. The 4 declared LLM stages need to be
> finished first (especially Design — that's the keystone). After that,
> Cost Advisor and Template Optimizer are the cheapest wins. The M-tier
> candidates require the **shared PR opener** before any of them ship —
> if we let each stage roll its own PR-creation logic, we'll fragment
> the rubberduck/judge surface and break docs-always-updated.
