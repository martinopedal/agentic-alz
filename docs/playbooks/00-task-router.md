# 00 — Task router

> **Read this before every task.** This is the only playbook the agent
> reads top-to-bottom on every run. It picks the right playbook for the
> task, then hands off.

## Triggers

- The agent is being assigned an issue, opening a chat session, or
  receiving a `@copilot` mention. **Always start here.**

## Steps

1. **Identify the task type from the trigger.** Use the table below.
   Pick the *first* row that matches; rows are ordered by precedence
   (incident > sensitive surface > behavioural change > docs).
2. **Open the chosen playbook.** Read it end-to-end before writing any
   diff.
3. **If two rows match,** the higher row wins; write a one-line note in
   the PR body's `## Playbook` section explaining which other playbook
   you also consulted.
4. **If no row matches,** stop and ask a human. Opening a roadmap item
   (`agent_eligible: false`, `human-only`) is the sanctioned escalation.

## Decision table

| If the task involves … | Then use playbook |
| --- | --- |
| The PR / issue carries the `incident` label | [`09-incident-response.md`](09-incident-response.md) |
| Editing `.github/workflows/apply.yml`, `bootstrap/`, or anything in the protected `prod` environment | **Stop.** Sensitive surface, never agent-eligible. Open a roadmap item; if you must, follow [`08-ci-workflow-change.md`](08-ci-workflow-change.md) as a human |
| Editing `prompts/`, `prompts/system/`, `schemas/`, `docs/models.allowlist.yaml`, or `docs/mcp.allowlist.yaml` | [`04-prompt-or-schema-change.md`](04-prompt-or-schema-change.md) |
| Editing anything under `policies/` | [`05-policy-change.md`](05-policy-change.md) |
| Editing anything under `templates/` | [`06-iac-template-change.md`](06-iac-template-change.md) |
| Adding or editing exemplars under `firewall-policy/lib/` | [`07-firewall-lib-exemplar.md`](07-firewall-lib-exemplar.md) |
| Editing any other `.github/workflows/*.yml` | [`08-ci-workflow-change.md`](08-ci-workflow-change.md) |
| Architectural decision touching one of the sensitive surfaces above | [`10-research-and-decide.md`](10-research-and-decide.md) (then the matching surface playbook) |
| The issue body carries `roadmap-id:` and you are the assignee | [`01-roadmap-item.md`](01-roadmap-item.md) |
| You are fixing a bug that has a reproducer | [`02-bug-fix.md`](02-bug-fix.md) |
| You are only editing markdown / comments and `docs/generated/` is untouched | [`03-doc-only.md`](03-doc-only.md) |

## How to use this in a PR description

The `## Playbook` section in
[`.github/PULL_REQUEST_TEMPLATE.md`](../../.github/PULL_REQUEST_TEMPLATE.md)
asks you to tick the playbook you followed. Tick **exactly one** primary
playbook; if you also consulted others, list them as a free-form
sub-bullet. The `rubberduck` workflow refuses PRs whose `## Playbook`
section is empty or whose primary tick is missing.

## Definition of Done

- [ ] You named exactly one primary playbook and (optionally) listed
      consulted secondaries in the PR's `## Playbook` section.
- [ ] You opened the chosen playbook and read it end-to-end before
      writing any diff.
- [ ] `rubberduck / check` passes (the section is non-empty).
- [ ] `ci / lint-instructions` passes (the playbook id you ticked
      exists under `docs/playbooks/`).

## References

- *Adding repository custom instructions for GitHub Copilot* — GitHub
  Docs. The `.github/copilot-instructions.md` and `AGENTS.md` contracts
  this router flows from. Retrieved 2026-05-08.
  <https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot>
- *About Copilot cloud agent (formerly Copilot coding agent)* — GitHub
  Docs. Retrieved 2026-05-08.
  <https://docs.github.com/en/copilot/concepts/about-copilot-coding-agent>
- *AGENTS.md — open format for agent instructions*. Retrieved 2026-05-08.
  <https://agents.md/>
