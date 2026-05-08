# Cloud-agent squad

The "squad" pattern (popularised by [@bradygaster][bg]) lets a small team
delegate well-scoped work to the GitHub Copilot **cloud agent** by turning a
machine-readable roadmap into one GitHub issue per work item, with the agent
auto-assigned where appropriate. This page documents the **bootstrapper**
(what it does, why, and how it stays idempotent). The per-task instructions
live under [`docs/playbooks/`](playbooks/) — start at
[`00-task-router.md`](playbooks/00-task-router.md).

> **Companion pages.** [`local-dev.md`](local-dev.md) covers running the
> deterministic pipeline on a developer laptop;
> [`copilot-developer-setup.md`](copilot-developer-setup.md) lists which
> Copilot CLI / VS Code / chat-mode / MCP features are sanctioned for
> this repo. The agent-instruction surface every Copilot session
> consults is [`AGENTS.md`](../AGENTS.md). The cloud agent is **the
> only sanctioned channel for an LLM to open a PR** — local developers
> must not have Copilot Chat or the Copilot CLI open PRs on their behalf
> as a workaround for the eligibility gates below.

[bg]: https://github.com/bradygaster

## Pieces

| Piece | Purpose |
| --- | --- |
| [`ROADMAP.md`](../ROADMAP.md) | Single source of truth for planned work. One H3 + ` ```yaml ` block per item. |
| [`schemas/roadmap.schema.json`](../schemas/roadmap.schema.json) | Validates the YAML metadata of every roadmap item. The optional `playbook:` field overrides the label-derived default. |
| [`scripts/squad_bootstrap.py`](../scripts/squad_bootstrap.py) | Parser, validator, and idempotent GitHub upserter. Has `--dry-run`. Injects a `Playbook:` link into each issue body. |
| [`docs/playbooks/`](playbooks/) | Per-task instruction sheets. The bootstrapper picks the right one from labels; `area:firewall` → 07, `area:ci` → 08, `area:llm`/`area:prompts`/`area:schemas` → 04, `area:security` → 05, `area:terraform`/`area:bicep` → 06; default `00-task-router.md`. |
| [`AGENTS.md`](../AGENTS.md) | The agent-instruction surface every Copilot session reads. The Copilot stub at [`.github/copilot-instructions.md`](../.github/copilot-instructions.md) points at it; CI verifies they stay in sync. |
| [`.github/workflows/squad.yml`](../.github/workflows/squad.yml) | Runs `--dry-run` on PRs and the real script on push to `main`, on a daily cron, and on `workflow_dispatch`. |
| [`.github/ISSUE_TEMPLATE/`](../.github/ISSUE_TEMPLATE/) | Disables blank issues; routes humans to `roadmap-item.yml`, `bug.yml`, or `change-request.yml`. None of these are auto-assigned to the agent. |
| [`.github/workflows/copilot-setup-steps.yml`](../.github/workflows/copilot-setup-steps.yml) | Cloud-agent environment accelerator. Preinstalls Python + the orchestrator (`pip install -e '.[dev]'`), Terraform, and Conftest before the agent starts a session, so agent runs match a contributor's local setup. |

## Idempotency contract

Each rendered issue body begins with an HTML comment marker:

```
<!-- roadmap-id: phase2-validate-workflow -->
```

The bootstrap script indexes every existing issue by that marker and decides:

* **create** — no issue carries the marker yet.
* **update** — an issue carries the marker but its body has drifted from what
  the roadmap currently renders.
* **noop** — body matches; nothing to do.

The script never closes or reopens issues. Closure (and reopening) stays a
human action so `depends_on` semantics remain auditable.

## Auto-assignment to `@copilot`

An item is assigned to the Copilot cloud agent **only when all four** hold:

1. `agent_eligible: true` in `ROADMAP.md`.
2. The item carries no `human-only` label (a label that lets you take work
   back without editing the roadmap).
3. Every entry in `depends_on` resolves to a **closed** issue.
4. `AGENTIC_ALZ_DISABLED` is not engaged.

The default for new items is `agent_eligible: false`. The following surfaces
**must** stay `agent_eligible: false` and **must** carry the `human-only`
label:

* `apply.yml` and anything that runs in the protected `prod` environment
* `bootstrap/` (Phase-1 identity provisioning)
* `policies/` (OPA conformance)
* `prompts/` (LLM prompts; gated by the multi-model judge)
* `schemas/` (typed contracts at stage boundaries)
* `docs/models.allowlist.yaml` (frontier-model allowlist)
* `docs/mcp.allowlist.yaml` (MCP server allowlist; see [`generated/mcp.md`](generated/mcp.md))

These are the surfaces the consensus plan (`docs/consensus-plan.md`) calls
out as destructive or LLM-sensitive. Roadmap items touching them remain
human-driven; the existing **rubberduck**, **multi-model judge**, and
**frontier-model attestation** gates still apply to whatever PRs eventually
land them.

## Bypassing auto-assignment in an emergency

Add the `human-only` label to the open issue. The next squad run will not
re-assign `@copilot`, even if the YAML still says `agent_eligible: true`. The
roadmap entry should then be edited to flip the flag so future regenerations
agree.

## Triggers

* **PR** touching `ROADMAP.md`, the script, the schema, or the workflow:
  `--dry-run` posts the planned diff into the PR job summary so reviewers
  see what would change before merge.
* **Push to `main`** of the same paths: real run.
* **Daily cron (06:00 UTC)**: picks up items whose dependencies have just
  closed.
* **`workflow_dispatch`**: manual re-run from the Actions tab.

The kill switch (`AGENTIC_ALZ_DISABLED` repo variable) halts both the
workflow and the script itself.

## Cloud agent vs. local developer

The squad pattern delegates **autonomous, scoped, agent-eligible** work
to the Copilot cloud agent. It does not replace local developers — the
two channels do different things:

| Channel | What it does | Where it runs |
| --- | --- | --- |
| Cloud agent (`@copilot` on a squad-bootstrapped issue) | Picks up a single roadmap item, opens a PR, responds to review feedback | Ephemeral GitHub-hosted runner with the env preinstalled by [`copilot-setup-steps.yml`](../.github/workflows/copilot-setup-steps.yml) |
| Local developer | Anything that is `agent_eligible: false` (sensitive surfaces above), exploratory work, multi-item refactors, and any change that needs the multi-model judge | Your laptop — see [`local-dev.md`](local-dev.md) |
| Copilot Chat / Copilot CLI on a developer laptop | Read-only exploration, drafting tests, drafting non-sensitive refactors. Author owns the diff. | Your laptop — see [`copilot-developer-setup.md`](copilot-developer-setup.md) |

Local Copilot sessions **must not** open PRs on your behalf as a way of
getting around the eligibility gates. If you want the agent to take a
piece of work, change the roadmap entry to `agent_eligible: true` on a
PR and merge it; the next squad run upserts the issue and assigns
`@copilot` deterministically.

## Future fan-out

The schema reserves a `repo` field for routing items to sibling repos
(`alz-platform`, `alz-firewall-policy`, `alz-workloads/<name>`). v1 ignores
the field and only operates on the current repo; cross-repo dispatch will
land alongside `phase1-sibling-repos`.
