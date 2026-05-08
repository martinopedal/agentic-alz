# Copilot developer setup (sanctioned features for this repo)

> **Audience:** humans contributing to `agentic-alz`. This page is a
> **policy statement**, not just a tutorial — it lists which GitHub
> Copilot surfaces are sanctioned for this repository, which are
> deliberately not used, and which paths must remain off-limits to chat-
> driven edits regardless of how convenient an LLM rewrite would be.
>
> **For agent-targeted instructions see [`AGENTS.md`](../AGENTS.md)** —
> that file is the single source of truth every cloud agent and local
> Copilot session reads. This page is the human policy mirror.
>
> If a section says `<TBD: NetSec to confirm>`, the default is the
> conservative interpretation (i.e. **not** sanctioned) until a NetSec /
> platform-team CODEOWNER signs off in a follow-up PR.

The companion pages are [`local-dev.md`](local-dev.md) (how to run the
deterministic pipeline on your laptop) and [`squad.md`](squad.md) (how
the cloud agent picks up roadmap items).

## 1. GitHub CLI + Copilot CLI

### `gh` CLI

The GitHub CLI is the only sanctioned client for opening PRs and
querying issues from a developer machine. Install per the official
docs and authenticate against the org you contribute under:

```bash
gh auth login --hostname github.com --git-protocol https --web
gh auth status
```

You should never need to push or merge from `gh` for sensitive paths
(see §4); branch protection on `main` enforces this.

### `gh-copilot` extension

`gh-copilot` is sanctioned for **shell-command suggestions only**. It
does not edit repository files. Install:

```bash
gh extension install github/gh-copilot
gh copilot --version
```

Use `gh copilot suggest` and `gh copilot explain` for shell / `git` /
Terraform / Azure CLI command help. Do **not** copy-paste its output
into commit messages, PR descriptions, or rubberduck sections without
review — it is not a frontier-allowlisted source. The repo's
multi-model judge governs LLM-authored content that goes into PRs (see
[`multi-model-judge.md`](multi-model-judge.md)).

### Standalone GitHub Copilot CLI

The newer standalone Copilot CLI (`copilot`, distinct from
`gh-copilot`) ships an interactive coding assistant. Sanctioned use in
this repo:

| Use | Sanctioned? |
| --- | :---: |
| Asking it to explain code in `orchestrator/`, `evals/`, `templates/`, `firewall-policy/lib/` | ✓ |
| Letting it draft test fixtures or non-sensitive refactors as a starting point for a PR | ✓ — but the PR author is fully responsible for the diff |
| Pointing it at sensitive paths (see §4) for any write-mode operation | ✗ |
| Letting it open PRs on your behalf without you reading the diff | ✗ |
| Letting it run `terraform apply`, `gh pr merge`, or any kill-switch-bypassing command | ✗ |

The general rule: any Copilot CLI invocation that **reads** is fine;
any invocation that **writes** must produce a diff you read line-by-line
before staging.

## 2. VS Code GitHub Copilot extension

Sanctioned features:

| Feature | Sanctioned? | Notes |
| --- | :---: | --- |
| Inline completions in `orchestrator/`, `evals/`, `templates/`, `firewall-policy/lib/` | ✓ | Standard developer aid. |
| Copilot Chat: explain / Q&A about any file | ✓ | Read-only; no diff written. |
| Copilot Chat: draft tests, refactor non-sensitive code | ✓ | Author owns the resulting diff. |
| Copilot Chat: edit files under sensitive paths (§4) | ✗ | Use a normal PR with the rubberduck and multi-model-judge gates. |
| `@workspace /fix`, `/tests`, `/explain` against non-sensitive paths | ✓ | Read or local-edit only. |
| Copilot Workspaces / agent mode opening a remote PR | ✗ — for **local** developers | The cloud agent is the sanctioned channel for that; see §3. |
| Suggesting changes to `.github/workflows/*.yml`, `bootstrap/`, `apply.yml` | ✗ | Workflow changes touch the apply path. |
| Suggesting changes to `prompts/`, `policies/`, `schemas/`, `docs/models.allowlist.yaml`, `docs/mcp.allowlist.yaml` | ✗ | These are LLM-governed surfaces — the multi-model judge gate applies. |

If Copilot Chat offers to edit a file inside a sensitive path, **decline
the suggestion** and open a regular PR instead.

## 3. Cloud agent (`@copilot`) — sanctioned channel for autonomous PRs

The Copilot cloud agent is the **only** sanctioned way to have an LLM
open a PR against this repo. Eligibility is enforced by
[`scripts/squad_bootstrap.py`](../scripts/squad_bootstrap.py):

1. Roadmap item declares `agent_eligible: true`.
2. The corresponding GitHub issue carries no `human-only` label.
3. Every `depends_on` resolves to a closed issue.
4. `AGENTIC_ALZ_DISABLED` is not engaged.

Local developers must **not** instruct a Copilot Chat or Copilot CLI
session to open a PR on their behalf as a workaround for an item the
squad declined to assign — the eligibility gates are the policy, not
the workflow. If you believe an item should be agent-eligible, change
`ROADMAP.md` on a PR; that is the sanctioned escalation path.

See [`squad.md`](squad.md) for the full picture.

## 4. Sensitive paths — never accept a chat-driven edit

These paths are CODEOWNED by the platform team / NetSec and require
human-authored changes with the rubberduck and multi-model-judge gates.
Even if Copilot's suggestion is correct, the PR must come from a human
who can attest to it.

| Path | Why it's sensitive |
| --- | --- |
| `apply.yml` and the protected `prod` environment | The only path that can mutate Azure. |
| `bootstrap/` | Phase-1 identity provisioning — wrong config breaks OIDC and forces a clean-up incident. |
| `policies/` | OPA conformance — silent gaps mean we ship unsafe Terraform. |
| `prompts/` | LLM prompts — multi-model-judge governs every change. |
| `schemas/` | Typed contracts at stage boundaries — schema drift breaks every downstream consumer. |
| `docs/models.allowlist.yaml` | Frontier-model allowlist — adding a model is a NetSec decision. |
| `docs/mcp.allowlist.yaml` | MCP server allowlist — adding `mode: write` is a NetSec decision. See [`mcp.md`](generated/mcp.md). |
| `.github/workflows/*.yml` (especially `apply.yml`, `copilot-setup-steps.yml`, `squad.yml`) | These define what CI and the cloud agent can do. |

Code in `orchestrator/agentic_alz/llm/` and `orchestrator/agentic_alz/mcp/`
is also sensitive — those are the runtime enforcement points for the two
allowlists. Drive-by Copilot rewrites here are not sanctioned.

## 5. Custom chat modes / skills / agents

| Mode / skill | Status | Notes |
| --- | :---: | --- |
| Custom **chat modes** that scope Copilot to a single directory or file pattern | <TBD: maintainer to confirm> | Default: not sanctioned. If used, restrict to non-sensitive paths only. |
| Custom **skills** that wrap Azure tooling (`az`, ARM what-if, Terraform module discovery) | <TBD: NetSec to confirm> | Any skill that issues network calls must mirror the MCP allowlist (see §6). |
| Custom **skills** that mutate Azure or repo state | ✗ | The only mutation paths are the deterministic CI workflows. |
| Custom **agents** running locally with persistent memory | <TBD: maintainer to confirm> | Default: not sanctioned. Local agents must respect the kill switch (§7). |
| Cloud agent custom instructions in `.github/copilot-instructions.md` or similar | <TBD: maintainer to confirm> | If added, must reference this file and `mcp.allowlist.yaml`. |

If you want a custom skill / agent / chat mode adopted repo-wide, open
a roadmap item for it (`agent_eligible: false`, `human-only`) and
include the threat-model implications in the rubberduck section.

## 6. MCP servers — runtime allowlist

LLM tool-use against MCP servers is gated by the runtime allowlist at
[`docs/mcp.allowlist.yaml`](mcp.allowlist.yaml) and the OPA policy at
[`policies/mcp_allowlist.rego`](../policies/mcp_allowlist.rego). The
generated table lives at [`generated/mcp.md`](generated/mcp.md).

For local developers:

* You may run any sanctioned MCP server **locally in `read` mode** for
  exploration. Output must never be pasted directly into a PR diff —
  round-trip through the relevant typed schema.
* You may not configure a Copilot Chat / Copilot CLI session to use an
  MCP server that is **not** in the allowlist while working on this
  repo, even for read-mode exploration. Adding a server is a PR.
* You may not configure any MCP server in `write` mode against this
  repo's working tree. The only sanctioned write-mode server is
  `github-mcp`, restricted to PR/issue tools and only used by the
  squad bootstrap and the future Drift Triage stage running in CI.

## 7. Kill switch interaction

Every Copilot-mediated action — local, cloud, MCP-driven — must respect
`AGENTIC_ALZ_DISABLED`. The orchestrator's
[`killswitch.py`](../orchestrator/agentic_alz/killswitch.py) is the
runtime check; the kill switch also halts the squad bootstrap workflow
and the apply workflow. If you're testing a Copilot integration that
issues commands on your behalf, verify it stops cleanly when
`AGENTIC_ALZ_DISABLED=true`.

## 8. When in doubt

Default to the conservative answer:

* **Read** — fine.
* **Write to a non-sensitive path** — fine, but you own the diff.
* **Write to a sensitive path (§4)** — open a normal PR with the
  rubberduck and multi-model-judge gates.
* **Mutate Azure or the GitHub apply path** — never via Copilot.
