# Local development

> **Audience:** contributors running the orchestrator on their own machine —
> humans driving the deterministic CLI, the eval harness, and the policy
> gates without touching Azure. For "what the cloud agent does" see
> [`squad.md`](squad.md); for "which Copilot features are sanctioned for
> this repo" see [`copilot-developer-setup.md`](copilot-developer-setup.md).

This page is the local mirror of what CI runs. If you can complete every
section below on your laptop, your PR will pass the same gates that CI
applies.

## Prerequisites

| Tool | Minimum version | Notes |
| --- | --- | --- |
| Python | 3.11 | Pinned in [`copilot-setup-steps.yml`](../.github/workflows/copilot-setup-steps.yml). |
| Terraform | 1.5+ (CI uses 1.9.8) | Required by `agentic-alz generate` smoke checks and lab mode. |
| Conftest (OPA) | 0.55+ (CI uses 0.56) | Required by [`policies/avm_pinning.rego`](../policies/avm_pinning.rego) and [`policies/mcp_allowlist.rego`](../policies/mcp_allowlist.rego). |
| `az` CLI | latest | Optional locally — only needed if you actually deploy. The deterministic CLI does not call Azure. |
| `gh` CLI | latest | Optional locally — used by the squad bootstrap, which only the cloud agent / CI runs in real mode. See [`copilot-developer-setup.md`](copilot-developer-setup.md). |

You do **not** need any LLM credentials to run the local pipeline; the
Interview, Design, Drift Triage, and Firewall Composer stages all have an
offline-deterministic path used by the eval harness.

## One-time setup

```bash
git clone https://github.com/martinopedal/agentic-alz.git
cd agentic-alz/orchestrator
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
```

This installs the `agentic-alz` CLI plus dev extras (pytest, ruff,
jsonschema, PyYAML). It is the same invocation that CI and the cloud
agent's [`copilot-setup-steps.yml`](../.github/workflows/copilot-setup-steps.yml)
run, so a green local run matches a green CI run.

Smoke-test:

```bash
agentic-alz --help
python -c "import agentic_alz, jsonschema, yaml, click; print('ok')"
```

## End-to-end against the golden fixture

Every command below runs offline, against
[`evals/golden/hns-minimal/`](../evals/golden/hns-minimal/), and never
touches Azure.

To run the same deterministic path as one local smoke test:

```bash
scripts/e2e-demo.sh
```

The script validates inputs, replays the offline interview fixture, generates
Terraform, classifies a saved plan fixture, checks the saved-plan Terraform
policy, creates a sandbox lab bundle, and replays all golden eval cases. See
[`deploy-readiness.md`](deploy-readiness.md) for what this proves and which
production deploy gaps remain human-owned.

```bash
# 1. Validate the inputs against schemas/inputs.schema.json.
agentic-alz validate-inputs evals/golden/hns-minimal/inputs.yaml

# 2. Render the hub-and-spoke template into a working directory.
agentic-alz generate \
  --inputs evals/golden/hns-minimal/inputs.yaml \
  --out /tmp/alz-out

# 3. Classify a saved Terraform plan against the v1 risk rubric.
agentic-alz risk \
  --plan-json orchestrator/tests/data/plan.sample.json \
  --env sandbox

# 4. Evaluate a Terraform CLI argv against the v1 safety policy
#    (this is what the apply workflow uses to refuse risky invocations).
agentic-alz tf-policy -- plan -out=tfplan
agentic-alz tf-policy -- apply tfplan
```

### Interview stage (offline)

The Interview stage parses a recorded conversation transcript and produces
a validated `inputs.yaml`. There is no LLM call in offline mode.

```bash
agentic-alz interview \
  --transcript evals/golden/interview-hns-minimal/transcript.jsonl \
  --out /tmp/inputs.yaml
```

The transcript intentionally contains a prompt-injection attempt and an
off-topic distractor; the `validate_llm_output` guard strips them before
the schema validator sees the result. See `prompts/interview.v1.md` and
`orchestrator/agentic_alz/stages/interview.py`.

Live mode (`--live --model <id>`) requires a model id present in
[`docs/models.allowlist.yaml`](models.allowlist.yaml) and currently raises
`LiveModeNotImplemented`; the provider client lands in a separate
human-merged PR.

### Lab mode (sandbox bundle)

```bash
agentic-alz lab init \
  --inputs evals/golden/lab-hns/inputs.yaml \
  --out /tmp/lab-bundle.tar.gz
```

Refuses any inputs whose `tags.defaults.Environment` is not `"sandbox"`
(exit 7), and strips the production `backend.tf` from the bundle. **Lab
mode never runs `terraform apply`** — the operator runs that themselves
out-of-band. See [`docs/lab-mode.md`](lab-mode.md).

## Running the same checks CI runs

Run these before pushing — they are exactly what the
[`ci`](../.github/workflows/ci.yml) and
[`docs`](../.github/workflows/docs.yml) workflows execute.

```bash
# Orchestrator unit tests (and coverage).
cd orchestrator && pytest

# Linter — no warnings allowed.
ruff check .

# Replay the eval harness against the golden runs.
cd .. && python evals/replay.py

# AVM-pinning policy on the hub-and-spoke template.
conftest test \
  --parser hcl2 \
  --policy policies \
  --namespace alz.avm_pinning \
  templates/hub-and-spoke/*.tf

# MCP allowlist shape policy on docs/mcp.allowlist.yaml.
conftest test \
  --parser yaml \
  --policy policies \
  --namespace alz.mcp_allowlist \
  docs/mcp.allowlist.yaml

# Auto-generated docs must be byte-identical to what the script produces.
python scripts/gen_docs.py --check
```

If `gen_docs.py --check` fails, regenerate and commit:

```bash
python scripts/gen_docs.py
git add docs/generated/
```

> Never hand-edit anything under `docs/generated/` — the
> [`docs`](../.github/workflows/docs.yml) workflow fails on any diff.

## Kill switch

Every CLI command and workflow respects
`AGENTIC_ALZ_DISABLED=true` and exits with `KillSwitchEngaged` (exit 2)
before any external side effect. To verify locally:

```bash
AGENTIC_ALZ_DISABLED=true agentic-alz validate-inputs \
  evals/golden/hns-minimal/inputs.yaml
echo "exit was $?"   # expect 2
```

## What runs where

| Action | Local laptop | Cloud agent / CI |
| --- | :---: | :---: |
| Deterministic CLI commands (`validate-inputs`, `generate`, `risk`, `tf-policy`, `lab init`, `interview --transcript`) | ✓ | ✓ |
| `pytest`, `ruff check .`, `python evals/replay.py`, `python scripts/gen_docs.py --check`, `conftest test ...` | ✓ | ✓ |
| `terraform plan` against a real Azure subscription | ✗ | ✓ (Phase-2 `validate.yml` + `plan.yml`) |
| `terraform apply` against a real Azure subscription | ✗ | ✓ (`apply.yml` only — protected `prod` environment) |
| LLM stages in `--live` mode | ✗ (until provider client lands) | ✗ (until provider client lands) |
| Squad bootstrap (`scripts/squad_bootstrap.py`) writing real GitHub issues | ✗ — `--dry-run` only | ✓ (`squad.yml` on push to `main` and daily cron) |

Local development never produces side effects on Azure or on the GitHub
issue tracker. If you need to test the squad bootstrap, use `--dry-run`:

```bash
python scripts/squad_bootstrap.py --dry-run --repo martinopedal/agentic-alz
```

## What to expect from the cloud agent

The Copilot cloud agent is **not** a substitute for the local workflow
above. It picks up GitHub issues created from
[`ROADMAP.md`](../ROADMAP.md) by the squad bootstrap, but **only** when
the roadmap item is `agent_eligible: true`, every `depends_on` is
closed, no `human-only` label is set, and `AGENTIC_ALZ_DISABLED` is off.
See [`docs/squad.md`](squad.md) for the full eligibility rules and the
list of surfaces (`prompts/`, `policies/`, `schemas/`, `apply.yml`,
`docs/models.allowlist.yaml`, `docs/mcp.allowlist.yaml`, …) that stay
human-only.

If you want the agent to handle a piece of work, the lever is: edit
`ROADMAP.md` on a feature branch, set `agent_eligible: true` for the
item, ensure the dependencies are met, and merge to `main`. The next
squad run upserts the issue and assigns `@copilot`.
