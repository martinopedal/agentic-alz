<!--
  Required PR template for Agentic ALZ.
  Both the Rubberduck and Judge sections are checked by
  .github/workflows/rubberduck.yml — leaving the placeholders in or omitting
  a heading will fail the PR.

  See docs/rubberduck.md and docs/multi-model-judge.md.
-->

## Summary

<!-- One paragraph: what this PR does and why, in plain language. -->

## Rubberduck

> This section is **required**. See [docs/rubberduck.md](../docs/rubberduck.md).
> Replace every `<...>` placeholder with at least one full sentence.

### What changed and why

<...>

### What I considered and rejected

<...>

### Blast radius

<...>

### Self-review notes

- <First thing I re-checked after writing the change>
- <Second thing I re-checked>
- <Third thing I re-checked>

## Multi-model judge

> Required for PRs touching `prompts/**`, `templates/**`, `policies/**`,
> `schemas/**`, ADRs, or `docs/models.allowlist.yaml`.
> Otherwise tick "Not required" and explain why in one line.
> See [docs/multi-model-judge.md](../docs/multi-model-judge.md).

- [ ] Judge run attached as `judge-verdicts.json` artifact, with
      verdicts from at least two distinct providers
- [ ] All rubric criteria PASS at the configured threshold
- [ ] Not required for this PR — rationale: <...>

## Frontier-model attestation

- [ ] Any LLM call referenced or added by this PR uses a model id present
      in [`docs/models.allowlist.yaml`](../docs/models.allowlist.yaml).
- [ ] No LLM call was added to a destructive path (apply, destroy, state mutation).

## Validation

- [ ] `pytest` and `ruff check .` pass locally
- [ ] `python evals/replay.py` passes if `templates/`, `schemas/`, or
      `policies/` changed
- [ ] `python scripts/gen_docs.py --check` shows no diff under `docs/generated/`

## Linked issues

<!-- Closes #..., Refs #... -->
