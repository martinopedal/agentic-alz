# 03 — Doc-only change

> Markdown / comment edits that do not change behaviour and do not touch
> `docs/generated/`. The lightest path through CI.

## Triggers

- Edits restricted to `*.md` outside `docs/generated/`, or to comments
  inside source files that do not change executable behaviour.
- No schema, prompt, policy, template, workflow, or config change is
  bundled.

## What disqualifies this playbook

This is not doc-only and you must reroute via the task router if any of
the following is true:

- A file under `docs/generated/` is in the diff (always a code change —
  edit the *source* and regenerate via `python scripts/gen_docs.py`).
- The change touches `AGENTS.md`, `.github/copilot-instructions.md`, or
  `prompts/system/agent-preamble.v1.md` — these are the agent-instruction
  surfaces and require `04-prompt-or-schema-change.md`.
- The change adds, removes, or renames a public behaviour described in
  prose (e.g. CLI flag docs, allowlist semantics) — re-route to the
  matching behavioural playbook.

## Steps

1. **Edit the source markdown only.** Never `docs/generated/` directly.
2. **Run the link / formatting checks locally.** `python scripts/gen_docs.py
   --check` must show no diff.
3. **Cross-link.** If you add a new section, link it from the page's
   table of contents and from any sibling page that mentions the topic.
4. **Citations.** Any fact that is not self-evident from the codebase
   must include a citation with a retrieval date — see existing pages
   under `docs/playbooks/` for the format.

## Definition of Done

- [ ] Diff contains only `*.md` files (or comments) and *no* file under
      `docs/generated/`.
- [ ] `docs / generate-and-check` passes.
- [ ] `ci / lint-instructions` passes.
- [ ] `rubberduck / check` passes (the four required sections may be
      brief but must be substantive — "blast radius: documentation only"
      is acceptable, "n/a" is not).

## References

- *About custom instructions for GitHub Copilot* — GitHub Docs (file
  format and locations). Retrieved 2026-05-08.
  <https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot>
- *Microsoft Style Guide — Top 10 tips for Microsoft style and voice* —
  Microsoft Learn. Used to keep tone consistent with surrounding docs.
  Retrieved 2026-05-08.
  <https://learn.microsoft.com/style-guide/top-10-tips-style-voice>
- `docs/rubberduck.md` — required PR practice.
- *Diátaxis — a systematic framework for technical documentation*.
  The mental model behind splitting reference (`docs/generated/`) from
  explanation (`docs/`). Retrieved 2026-05-08. <https://diataxis.fr/>
