# SKILL: drift-to-roadmap-promotion

**Owner:** Holden (Lead)
**Created:** 2026-05-13
**Pattern:** Promote a discovered baseline drift from supporting infrastructure to ranked roadmap #1

---

## When to use

When a coordinator or team member discovers that an item previously classified as
"supporting infrastructure" or "unranked" is actually an active compliance violation
or baseline drift — and the team has a standing directive that the drift violates.

---

## Checklist

1. **Verify the drift is real.** Run the relevant check command (e.g.,
   `python scripts/gen_docs.py --check`) and confirm the failure is on the default
   branch, not introduced by a feature branch.

2. **Map to a standing directive.** Find the team decision (in `.squad/decisions.md`
   or equivalent) that the drift violates. If no standing directive exists, the drift
   is a bug, not a promotion trigger — use `02-bug-fix.md` instead.

3. **Re-rank, don't expand the pool.** Swap the promoted item into position #1 and
   shift the others down. Do NOT add a new item to the top-N just to make room.
   Rationale: the synthesis already evaluated the full candidate set; swapping
   preserves that evaluation while reflecting new urgency.

4. **Update the item's classification.** Change from "supporting infrastructure" to
   a first-class roadmap entry with full schema-validated metadata (id, title,
   milestone, summary, acceptance_criteria, labels, agent_eligible, depends_on).

5. **Set depends_on: [] (no deps).** An active drift fix is urgent and should not
   wait on other items. If the fix genuinely depends on another item, that dependency
   must also be expedited.

6. **Document the promotion rationale.** In the decision file and history, record:
   - What was discovered (the drift)
   - Who discovered it (coordinator, CI, manual check)
   - Which standing directive it violates
   - Why the original classification was wrong (missing evidence at synthesis time)

## Anti-patterns

- **Don't promote without evidence.** A theoretical risk is not a drift. The check
  must be failing on the default branch right now.
- **Don't expand the top-N pool.** Promoting item X means demoting item N — accept
  the tradeoff, don't inflate the batch.
- **Don't skip schema validation.** The promoted item must validate against the
  roadmap schema just like any other entry. Urgency is not an excuse for sloppy
  metadata.

---

**End of skill doc.**
