# Rubberduck-every-change

> "Rubberducking" is the practice of explaining a change, in writing, to an
> imaginary newcomer before asking a human reviewer to read it. It catches
> bugs, surfaces hidden assumptions, and slashes review-cycle time. Agentic
> ALZ requires it on **every** PR.

## Hard rule

Every PR opened against `main` in this repo (and the sibling `alz-platform`,
`alz-firewall-policy`, `alz-workloads/*` repos) must contain a populated
**Rubberduck** section in the PR body. The
[`.github/PULL_REQUEST_TEMPLATE.md`](../.github/PULL_REQUEST_TEMPLATE.md)
provides the structure. The
[`rubberduck` workflow](../.github/workflows/rubberduck.yml) fails the PR if
the section is missing or left as the template placeholder.

## What "populated" means

The section has four required parts. Each must be at least one full sentence;
empty bullets, "see commit", "n/a", and the literal placeholder text all fail
the check.

1. **What changed and why** — one paragraph, plain language. No code; no jargon
   that a new joiner could not Google in 30 seconds.
2. **What I considered and rejected** — at least one alternative you ruled out
   and the reason. If you ruled out nothing, say so explicitly with a
   one-sentence justification.
3. **Blast radius** — which states, identities, environments, or sibling
   repos this change can affect on the worst day. For pure-doc changes the
   answer is usually "none, documentation only", which is fine — write it.
4. **Self-review notes** — three concrete things you re-read and confirmed
   correct after writing the change (e.g. "I re-checked that the OPA rule
   denies wildcard ports", "I verified versions.lock still matches every
   `module` block").

## When you cannot rubberduck (incident response)

During Sev-1/Sev-2 incident response (see
[`incident-response.md`](incident-response.md)) the rubberduck check is
bypassed by adding the label `incident` to the PR. The PR description must
still contain a one-line incident reference; the post-incident review step
back-fills the full rubberduck.

## Why on every change, even the "obvious" ones?

Three reasons, all from this repo's own threat model:

- **Prompt-injection-shaped diffs.** A two-line change to a prompt file can
  silently widen the LLM's tool surface. Rubberducking forces the author to
  state the new boundary in their own words.
- **Eventual-consistency landmines.** A "trivial" rename may invalidate a
  poll target documented in [`eventual-consistency.md`](eventual-consistency.md).
  The rubberduck section gives the reviewer somewhere to look first.
- **Cost surprises.** Infracost catches the obvious. The rubberduck catches
  the "we just enabled DDoS Standard on a stub VNet" class.

## Rubberduck vs multi-model judge

These are complementary, not redundant:

- **Rubberduck** is the *author* explaining the change in human language. It
  is required on every PR.
- **Multi-model judge** (see [`docs/multi-model-judge.md`](multi-model-judge.md))
  is asked of N allow-listed frontier models against a **fixed rubric** for
  PRs that touch prompts, golden templates, OPA policies, or ADRs. It is
  required on those classes of PR; optional otherwise.

## Mapping rubberduck subsections to playbook Definition-of-Done items

The four rubberduck subsections are deliberately the same shape across every
playbook, so a reviewer can read them in the same order regardless of the
PR's surface. The mapping below is what the `lint-instructions` job assumes:

| Rubberduck subsection | Maps to which playbook item |
| --- | --- |
| `### What changed and why` | The "Steps" section of the chosen playbook — paraphrase the step you actually performed, not the full procedure. |
| `### What I considered and rejected` | For sensitive surfaces, this is where you cite the `decision/<id>/` folder produced by [`10-research-and-decide.md`](playbooks/10-research-and-decide.md); for other PRs, it is the alternative implementations you ruled out. |
| `### Blast radius` | The same surface table that drove your playbook choice — cite which sensitive paths your PR does and does not touch. For doc-only PRs, "documentation only" is acceptable. |
| `### Self-review notes` | One bullet per Definition-of-Done item from your playbook that you re-checked manually after writing the diff. The CI gates already enforce most items; the bullets here are the ones you verified by hand. |

If you cannot fill a subsection without reaching for "n/a", you have probably
picked the wrong playbook — re-route via
[`00-task-router.md`](playbooks/00-task-router.md).
