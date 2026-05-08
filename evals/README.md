# Eval harness

The eval harness gates merges to `main`. There are two layers:

1. **Offline replay** (`replay.py`). Runs every deterministic stage against
   each golden case under `golden/`. Cheap, ~seconds, no Azure, no LLM. This
   layer runs on every PR via `.github/workflows/eval.yml`.
2. **Spend-capped sandbox deploy** (production). Runs `validate → plan →
   apply → terraform destroy` against the `eval-sandbox` Azure subscription.
   Gated on the `eval-sandbox` GitHub Environment with required reviewers
   and a hard spend cap at the EA/MCA level. Skeleton only in v1; turn on
   once Phase 0 is complete.

## Adding a golden case

```
evals/golden/<name>/
  inputs.yaml      # required; validated against schemas/inputs.schema.json
  plan.json        # optional; if present, risk classifier is exercised
  expected/        # optional; future: snapshot of generated terraform.tfvars.json
```

Cases must be small and unambiguous: one architecture decision per case,
not a kitchen-sink test. The point is to detect drift in the *deterministic*
stages when prompts, schemas, or templates change.

## Model upgrades

Production runs (when enabled) record golden-run pass rate per model
version. A new model is promoted only when its pass rate meets or exceeds
the prior model's on the full golden suite.
