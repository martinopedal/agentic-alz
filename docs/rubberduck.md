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
