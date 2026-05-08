# 01 — Roadmap item (squad-bootstrapped issue)

> The Copilot cloud agent has been auto-assigned to a GitHub issue whose
> body carries `<!-- roadmap-id: <id> -->`. This playbook is how to
> close that issue with a passing PR.

## Triggers

- An issue carries `<!-- roadmap-id: <id> -->` in its body.
- The issue is assigned to `@copilot` (or an agent acting under that
  identity).
- The issue body's `Playbook:` line either points here or is unset.

## Steps

1. **Verify eligibility locally.** Read `ROADMAP.md` and find the entry
   whose `id:` matches the marker. Confirm:
   - `agent_eligible: true`
   - the issue carries no `human-only` label
   - every entry in `depends_on` resolves to a closed issue
   - the kill switch (`AGENTIC_ALZ_DISABLED`) is not engaged
   If any condition fails, comment on the issue and stop.
2. **Branch.** Use the agent's default branch naming (`copilot/<short>`).
   Do not push to `main`; branch protection enforces this and the agent
   must never attempt to circumvent.
3. **Open a draft PR early.** Reference the issue with `Refs #<n>` (not
   `Closes`) in the PR body until your last commit, so the issue stays
   open while CI runs and a human can intervene.
4. **Commit-message convention.** Each commit message must include the
   line `roadmap-id: <id>` (lower-case) so the squad bootstrap can
   correlate the work.
5. **Run the per-area playbook.** The `Playbook:` line in the issue body
   names which surface-specific playbook applies (router → 04 / 05 /
   06 / 07 / 08). Read that one too before writing the diff.
6. **Local validation.** Run, in order: `cd orchestrator && pytest`,
   `ruff check .`, `python evals/replay.py`, `python scripts/gen_docs.py
   --check`, and any conftest invocation listed in the per-area
   playbook.
7. **Fill in the PR template.** All four required sections —
   `## Rubberduck`, `## Multi-model judge`, `## Frontier-model
   attestation`, `## Playbook` — must be populated. Empty placeholders
   fail the rubberduck workflow.
8. **Call `report_progress` after each meaningful step.** This is how
   the agent commits and pushes; never use `git push` directly.
9. **Close the issue with the merge.** The final commit may use
   `Closes #<n>` once the diff is review-ready.

## Acceptance-criteria mapping

The bootstrapped issue body has an `## Acceptance criteria` checklist
mirrored from `ROADMAP.md`. Tick each box only when it is *actually*
satisfied — the next squad-bootstrap run will reset bodies that drift
from `ROADMAP.md`, but acceptance ticks live on the issue itself and
are how a human reviewer audits completeness.

## Definition of Done

- [ ] Every acceptance criterion on the issue body is ticked.
- [ ] `ci / kill-switch check` passes.
- [ ] `ci / orchestrator (lint + test)` passes.
- [ ] `ci / schemas (validate examples)` passes.
- [ ] `ci / OPA policies (rego syntax + unit)` passes.
- [ ] `ci / lint-instructions` passes.
- [ ] `docs / generate-and-check` passes (no diff under `docs/generated/`).
- [ ] `rubberduck / check` passes (all four required sections populated).
- [ ] `eval / offline` passes if templates / schemas / policies were
      touched.

## References

- `ROADMAP.md` and `schemas/roadmap.schema.json` — the source of truth
  for what the agent may pick up.
- `docs/squad.md` — eligibility rules and idempotency contract.
- *About Copilot cloud agent (formerly Copilot coding agent)* — GitHub
  Docs. Retrieved 2026-05-08.
  <https://docs.github.com/en/copilot/concepts/about-copilot-coding-agent>
- *About custom instructions for GitHub Copilot coding agent* — GitHub
  Docs. The cloud-agent `copilot-setup-steps.yml` contract that
  preinstalls this repo's tooling. Retrieved 2026-05-08.
  <https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/customize-the-agent-environment>
- *Cloud Adoption Framework — Azure landing zones* — Microsoft Learn.
  The architectural baseline this repo automates. Retrieved 2026-05-08.
  <https://learn.microsoft.com/azure/cloud-adoption-framework/ready/landing-zone/>
