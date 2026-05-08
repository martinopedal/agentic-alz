# 02 — Bug fix

> Smallest possible diff that turns one failing test green. Anything
> beyond that is a separate PR.

## Triggers

- An issue, comment, or test failure that describes a defect with a
  reproducer (or a reproducer is reachable in two reads of the
  codebase).

## Steps

1. **Reproduce first.** Add a failing regression test *before* touching
   the code under test. The test must fail for the right reason; if it
   passes against `main`, you have not actually reproduced the bug.
2. **Minimum-edit fix.** Change as few lines as possible to make the
   test pass. Resist refactors, renames, formatting passes — they
   belong in their own PR.
3. **No drive-by.** If you find adjacent issues, open issues for them;
   do not bundle. Drive-by changes muddy the rubberduck and the judge.
4. **Re-run the full suite.** `cd orchestrator && pytest && ruff check
   .` then `python evals/replay.py` if you touched any path the eval
   harness covers.
5. **Sensitive surface.** If the fix requires editing a sensitive path
   (per `AGENTS.md`), stop here and re-route via the task router; this
   playbook does not authorise sensitive-surface edits.
6. **Document the bug, not the fix.** The PR's `## Summary` should
   describe the *user-visible defect* and the *trigger condition*. The
   diff explains the fix.

## Definition of Done

- [ ] A regression test that fails on the parent commit and passes on
      the fix commit is included.
- [ ] `ci / orchestrator (lint + test)` passes.
- [ ] `ci / schemas (validate examples)` passes if a schema-validated
      input is involved.
- [ ] `ci / lint-instructions` passes.
- [ ] `rubberduck / check` passes.
- [ ] `eval / offline` passes if the bug touched a schema, prompt,
      template, or policy path.
- [ ] No file outside the bug's blast radius is modified.

## References

- *Test-driven bug fixing* — Martin Fowler, refactoring.com (background
  reading on regression-test-first). Retrieved 2026-05-08.
  <https://martinfowler.com/articles/regressionGuide.html>
- *Cloud Adoption Framework — Operational excellence guidance* —
  Microsoft Learn. Justifies the minimal-diff rule for ALZ-adjacent
  changes. Retrieved 2026-05-08.
  <https://learn.microsoft.com/azure/cloud-adoption-framework/manage/considerations/protect>
- `docs/rubberduck.md` — the *Self-review notes* bullets must call out
  the regression test by name.
- *OWASP Top 10 for LLM Applications (2025) — LLM02 Insecure Output
  Handling*. Why every regression test gets paired with a typed schema
  assertion when the bug is in an LLM-stage output. Retrieved 2026-05-08.
  <https://owasp.org/www-project-top-10-for-large-language-model-applications/>
