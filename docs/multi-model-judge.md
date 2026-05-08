# Multi-model judge (build-time consensus)

> Per the consensus plan §4 ("Multi-model usage at *build time* (not
> runtime)"), Agentic ALZ uses multi-model consensus as a **planner + judge**
> pattern at PR-review time only. It is **never** a runtime safety mechanism.
> Runtime safety lives in typed schemas, `terraform plan`, Checkov, Infracost,
> OPA, and human approval through a protected GitHub Environment.

## When the judge is required

The judge is required on PRs that touch any of:

- `prompts/**`
- `templates/**`
- `policies/**`
- `schemas/**`
- ADRs under `docs/adr/**` (when added)
- `docs/models.allowlist.yaml`

It is optional but recommended for substantive design changes elsewhere.

## How it works

1. The PR author (or the orchestrator on their behalf) sends the candidate
   artefact, plus the fixed rubric below, to **N allow-listed frontier
   models** chosen from at least **two distinct providers**. This diversity
   requirement is enforced by code (see
   `orchestrator/agentic_alz/llm/judge.py`); single-provider "consensus" is
   refused.
2. Each model returns one structured JSON document scoring every rubric
   criterion as `pass` or `fail`, with a one-sentence rationale per
   criterion.
3. The aggregator (`agentic-alz judge <verdicts.json>`) is **deterministic**
   given those verdicts. It produces a `ConsensusReport` with PASS/FAIL per
   criterion. Default threshold is **unanimous**; PRs may opt down to
   majority for low-risk artefacts but not below.
4. Any `FAIL` blocks the PR and surfaces the dissenting model + rationale in
   a comment. There is no automatic retry; a human resolves the disagreement.

## Rubric (v1, fixed)

The rubric is intentionally short and stable. Adding a criterion is itself a
PR that runs the judge against the rubric change.

| Criterion | The model is asked: |
| --- | --- |
| `cost` | Does this change avoid surprising the operator on the next monthly bill (no new SKUs, no widened SKU tier, no new always-on PaaS)? |
| `policy` | Does this change pass every OPA rule in `policies/`, including `avm_pinning`, `alz_conformance`, `firewall_rules`, `naming`? |
| `naming` | Does every introduced resource name match `inputs.naming.pattern` and stay within Azure length limits? |
| `version-pinning` | Does every Terraform module use an exact semver and appear in the appropriate `versions.lock`? |
| `alz-conformance` | Does this change preserve the ALZ Accelerator + AVM contract (management-group placement, diagnostic settings, mandatory tags)? |

## Approved judge models

The set of models eligible to play the judge role is the subset of
`docs/models.allowlist.yaml` whose `role` includes `judge`. As of this
writing that is:

- `anthropic/claude-opus-4.7`
- `anthropic/claude-opus-4.6`
- `openai/gpt-5.4`
- `openai/gpt-5.3-codex`
- `google/gemini-2.5-pro`

A judge invocation must include at least one model from at least two
different providers.

## What the judge is NOT

- It is not a runtime gate. Apply still requires a human in a protected
  environment.
- It is not a substitute for the rubberduck section.
- It is not a substitute for OPA, Checkov, Infracost, or `terraform plan`.
- It does not "vote" on safety-critical questions on its own — any FAIL is
  escalated to a human, never overridden by majority.
