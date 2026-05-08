# orchestrator

Python package implementing the deterministic stages and safety primitives of
Agentic ALZ. See the [repo README](../README.md) and
[`docs/consensus-plan.md`](../docs/consensus-plan.md) for the full design.

## Local development

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
pytest
ruff check .
```

## CLI surface

```text
agentic-alz validate-inputs <path>
agentic-alz generate --inputs <path> --out <dir>
agentic-alz risk --plan-json <path> --env {sandbox,platform,workload}
agentic-alz tf-policy <argv...>
```

LLM stages (Interview, Design, Drift Triage, Firewall Composer) are exercised
through the orchestrator runtime, not the CLI; the CLI only exposes the
deterministic stages so they can be wired into CI.
