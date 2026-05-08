# 09 — Incident response

> Sev-1 / Sev-2 only. The `incident` label bypasses the rubberduck
> check; back-fill is mandatory in the post-incident review.

## Triggers

- An open Sev-1 or Sev-2 incident per `docs/incident-response.md`.
- A PR that legitimately needs to skip the rubberduck gate to land a
  fix faster than the gate would allow.

## Who can apply the `incident` label

The `incident` label may be applied only by:

- A repository maintainer (CODEOWNERS).
- An on-call SRE/IC named in the active incident channel.

A cloud agent may **never** apply this label. If an agent thinks an
incident bypass is warranted, it must comment on the PR and stop —
applying the bypass is a human decision.

## Steps

1. **Open the incident first.** Confirm there is an entry in the
   incident tracker and a Sev assignment. If there is not, this is not
   an incident and you must not apply the label.
2. **Smallest possible diff.** Strict minimum to mitigate. No
   refactors, no drive-by fixes, no opportunistic cleanups.
3. **Apply the `incident` label.** This bypasses the rubberduck gate.
   Every other gate (CI, OPA, eval, docs) still runs and must pass.
4. **Reference the incident** in the PR body's `## Summary` with a
   one-line link to the incident record.
5. **Back-fill the rubberduck.** Within 48 hours of incident closure,
   open a follow-up PR that retro-fits the four required rubberduck
   subsections to the incident PR's history (a comment-only follow-up
   PR is acceptable). The post-incident review template in
   `docs/incident-response.md` lists this as a required action item.
6. **Never bypass anything else.** The `incident` label bypasses
   *only* the rubberduck check. It does not bypass kill switch, OPA,
   schema validation, or branch protection.

## Definition of Done

- [ ] An open Sev-1 / Sev-2 incident is referenced in `## Summary`.
- [ ] The `incident` label is applied.
- [ ] `ci / kill-switch check` passes.
- [ ] `ci / orchestrator (lint + test)` passes (or the change is
      docs-only and `docs / generate-and-check` passes instead).
- [ ] `ci / OPA policies (rego syntax + unit)` passes if any policy
      surface is touched.
- [ ] `ci / lint-instructions` passes.
- [ ] A back-fill rubberduck PR is filed within 48 hours of incident
      closure.

## References

- `docs/incident-response.md` — incident severity matrix, on-call
  contract, post-incident review template.
- `docs/rubberduck.md` — the gate this playbook bypasses; lists the
  back-fill obligation.
- *NIST SP 800-61 Rev. 2 — Computer Security Incident Handling Guide*.
  The standard this repo's incident response is modelled on.
  Retrieved 2026-05-08.
  <https://csrc.nist.gov/publications/detail/sp/800-61/rev-2/final>
- *Google SRE Book — Managing Incidents*. Background reading on the
  smallest-diff-during-active-incident rule. Retrieved 2026-05-08.
  <https://sre.google/sre-book/managing-incidents/>
- *About Copilot cloud agent (formerly Copilot coding agent)* — GitHub
  Docs. Why the cloud agent is excluded from incident bypass paths.
  Retrieved 2026-05-08.
  <https://docs.github.com/en/copilot/concepts/about-copilot-coding-agent>
