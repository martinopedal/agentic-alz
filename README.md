# agentic-alz

Multi-stage GitOps orchestrator that helps a Cloud Solution Architect bring up
and operate an Azure Landing Zone (ALZ Accelerator + Azure Verified Modules +
Terraform), with narrow LLM-powered stages for interview, design, drift triage
and firewall change composition.

> Status: **v1 scaffolding**. This repository implements the structure,
> schemas, prompts, golden Terraform templates, OPA policies, orchestrator
> skeleton and CI for the consensus plan in
> [`docs/consensus-plan.md`](docs/consensus-plan.md). Real Azure deploys
> require completing the [Phase-0 prerequisites](docs/phase-0-prerequisites.md)
> first.

## Why "deterministic pipeline with narrow LLM stages"?

LLMs draft, humans approve, CI applies. Apply is never an LLM action. Runtime
safety comes from typed schemas, `terraform plan`, Checkov, Infracost,
policy-as-code (OPA/Conftest) and human approval through a protected GitHub
Environment — not from "consensus" between models.

## Repo layout

```
.
├── orchestrator/      # LangGraph app: stages, checkpointing, kill switch
├── prompts/           # Versioned prompt files (one per LLM stage)
├── schemas/           # JSON Schemas: inputs, design, risk, versions.lock
├── templates/         # Golden Terraform (hand-built, AVM-pinned)
├── policies/          # OPA/Conftest ALZ conformance rules
├── evals/             # Golden runs + replay harness
├── bootstrap/         # Phase-1 idempotent bootstrap (state SA, OIDC, repos)
├── firewall-policy/   # Shape of the sibling alz-firewall-policy repo
├── docs/              # Plan, prerequisites, runbook, threat model, ADRs
└── .github/workflows/ # validate, plan, apply, drift, cost, eval, ci
```

The sibling repos (`alz-platform`, `alz-firewall-policy`,
`alz-workloads/<name>`) are described in the consensus plan and bootstrapped by
[`bootstrap/phase1.sh`](bootstrap/phase1.sh).

## Quick start (development, no Azure required)

```bash
cd orchestrator
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
pytest
ruff check .
```

To exercise the pipeline against example inputs without touching Azure or any
LLM provider:

```bash
agentic-alz validate-inputs evals/golden/hns-minimal/inputs.yaml
agentic-alz generate --inputs evals/golden/hns-minimal/inputs.yaml --out /tmp/alz-out
agentic-alz risk --plan-json /tmp/plan.json
```

## Production prerequisites

See [`docs/phase-0-prerequisites.md`](docs/phase-0-prerequisites.md). Until
Phase 0 is complete, this orchestrator can only generate, validate and lint
Terraform — it cannot apply.

## License

[MIT](LICENSE)
