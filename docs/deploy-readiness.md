# Deploy readiness

This repository can already run the deterministic, no-Azure path end to end:
offline interview replay, input validation, Terraform generation, risk
classification, Terraform command-policy checks, lab bundle creation, and eval
replay. It is not yet a one-command production deploy system; the remaining
production gaps are tracked below so work can continue safely across multiple
passes.

## What works now

- `agentic-alz interview --transcript` converts a recorded transcript into a
  schema-valid `inputs.yaml` without calling an LLM provider.
- `agentic-alz validate-inputs` validates operator-supplied or replayed inputs.
- `agentic-alz generate` renders the `hub-and-spoke` AVM-pinned Terraform
  working directory.
- `agentic-alz risk` classifies a saved Terraform plan JSON with a deterministic
  risk rubric.
- `agentic-alz tf-policy` enforces the saved-plan flow used by CI before
  Terraform commands run.
- `agentic-alz lab init` creates a sandbox-only local-state bundle for demos and
  training.
- `python evals/replay.py` exercises all golden deterministic cases.

Run the full local path with:

```bash
cd /path/to/agentic-alz
cd orchestrator
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
cd ..
scripts/e2e-demo.sh
```

The script writes only to `/tmp` by default and does not call Azure, Terraform
`apply`, GitHub APIs, or any LLM provider.

## Remaining gaps for production deploy

| Gap | Current status | Pickup path |
| --- | --- | --- |
| Phase-0 Azure prerequisites | Documented as required before real deploys | Human verifies `docs/phase-0-prerequisites.md` and completes the tracked `phase0-*` roadmap items |
| Phase-1 identity, OIDC, backend, and sibling repo bootstrap | Deliberately human-only because it provisions identity and protected repos | Human-owned `phase1-*` roadmap items |
| Saved-plan production apply | Guardrail says apply is never an LLM action | Human-owned `phase2-apply-workflow` item and protected `prod` environment |
| Live LLM interview provider | Offline transcript path works; live mode raises `LiveModeNotImplemented` | Human-owned `llm-interview-runtime` because it touches live provider wiring and prompt-governed behavior |
| Design, Drift Triage, and Firewall Composer runtimes | Prompts and schemas exist, but deterministic runtime stages are not complete | Human-owned LLM-stage roadmap items unless narrowed to non-sensitive orchestrator-only work |
| Broader use cases | Golden cases cover hub-and-spoke minimal, interview replay, and lab mode | Add non-sensitive golden cases after dependencies are ready; sensitive prompt/schema/template changes require the matching playbook |

## Agent-safe next steps

- Add more deterministic golden cases that reuse existing schemas and templates.
- Improve local documentation and examples around `scripts/e2e-demo.sh`.
- Add orchestrator-only tests for already-implemented deterministic stages.
- Keep any changes to `prompts/`, `schemas/`, `policies/`, `templates/`,
  `.github/workflows/`, `bootstrap/`, and `firewall-policy/` on the required
  human playbook path.

## Human-only next steps

- Approve and verify Phase-0 and Phase-1 Azure prerequisites.
- Finalize production backend and sibling repository bootstrap.
- Complete the protected saved-plan apply path.
- Implement live model-provider clients and the remaining LLM runtimes under
  the multi-model judge process.
