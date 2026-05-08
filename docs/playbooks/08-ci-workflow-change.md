# 08 — CI workflow change

> **Sensitive surface.** `.github/workflows/*.yml` defines what CI and
> the cloud agent can do. Wrong here and the apply path silently
> widens. **Never agent-eligible.** Least-privilege tokens, explicit
> `permissions:` block, kill-switch short-circuit, SHA-pinned actions.

## Triggers

- Diff includes any file under `.github/workflows/`.
- Diff includes `.github/copilot-instructions.md` or
  `.github/PULL_REQUEST_TEMPLATE.md` (these files change CI behaviour
  via the `rubberduck` workflow even if they are markdown).

## Pre-flight

- **Never edit `apply.yml`** without `10-research-and-decide.md` first
  and a NetSec CODEOWNER on the PR. The apply workflow is the only
  path that can mutate Azure.
- **Never edit `copilot-setup-steps.yml`** without confirming the
  cloud agent can still complete `01-roadmap-item.md` end-to-end.

## Steps (human-author only)

1. **Top-level `permissions:` block.** Every workflow must declare
   minimum permissions at the top. Default to `contents: read`. Add
   `pull-requests: write` only if the workflow opens / comments on
   PRs; never `contents: write` unless the workflow legitimately
   pushes commits (and even then, never to `main`).
2. **Kill-switch step first.** Every workflow's first job (or every
   job's first step in matrix workflows) must check
   `AGENTIC_ALZ_DISABLED` and exit cleanly when engaged.
3. **SHA-pin third-party actions.** `uses: actions/checkout@v4` is
   acceptable for `actions/*` (first-party). Anything else must be
   SHA-pinned (`uses: org/action@<40-char-sha>`); tag-pinning a
   third-party action is forbidden — supply-chain risk.
4. **No `pull_request_target` without justification.** The default
   `pull_request` event is safe; `pull_request_target` runs untrusted
   code with elevated tokens and is forbidden unless the PR explicitly
   justifies it under `## Blast radius`.
5. **Concurrency.** Add a `concurrency:` block keyed by PR number /
   ref so duplicate runs cancel; the pattern is consistent across
   `ci.yml`, `docs.yml`, `rubberduck.yml`.
6. **Path filters mirror CODEOWNERS.** A workflow that runs only on
   `templates/**` should mirror that in CODEOWNERS so that the same
   reviewer set is required.
7. **Document.** A top-of-file comment must state the workflow's
   purpose, its trigger, what it gates, and what bypass label (if any)
   exists.

## Definition of Done

- [ ] Top-level `permissions:` block present and minimum.
- [ ] First job / step honours `AGENTIC_ALZ_DISABLED`.
- [ ] All third-party actions SHA-pinned.
- [ ] `concurrency:` block present and ref-keyed.
- [ ] `ci / kill-switch check` passes.
- [ ] `ci / orchestrator (lint + test)` passes.
- [ ] `ci / lint-instructions` passes.
- [ ] `rubberduck / check` passes; `## Blast radius` enumerates which
      paths the workflow gates and which bypasses it allows.
- [ ] CODEOWNERS reviewer (platform / NetSec) approved.

## References

- *GitHub Actions — Security hardening for workflows* — GitHub Docs.
  The least-privilege and SHA-pinning guidance this playbook codifies.
  Retrieved 2026-05-08.
  <https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions>
- *About Copilot cloud agent (formerly Copilot coding agent)* — GitHub
  Docs. The `copilot-setup-steps.yml` contract. Retrieved 2026-05-08.
  <https://docs.github.com/en/copilot/concepts/about-copilot-coding-agent>
- *OWASP Top 10 for LLM Applications (2025) — LLM05 Supply Chain
  Vulnerabilities*. Justifies SHA-pinning third-party actions.
  Retrieved 2026-05-08.
  <https://owasp.org/www-project-top-10-for-large-language-model-applications/>
- *Azure deployment stacks (Bicep)* — relevant when the future Bicep
  flavour's apply legs are added. Retrieved 2026-05-08.
  <https://learn.microsoft.com/azure/azure-resource-manager/bicep/deployment-stacks>
