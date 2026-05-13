# SKILL: hide-internal-tooling-behind-maintainer-area

**Owner:** Holden (Lead / Architect)  
**Created:** 2026-05-13  
**Pattern:** Documentation visibility governance for mixed product + team-coordination surfaces

---

## What this skill does

Provides a reusable pattern for hiding internal coordination / maintenance tooling from the public product surface while keeping it accessible to maintainers. Solves the problem: "How do I document internal team processes without polluting the end-user-facing docs or confusing the product narrative?"

This skill is a **documentation governance pattern**, not code. It involves:
- Adding a disambiguating clarifier in the existing public doc (one-liner)
- Creating a collapsed maintainer-area `<details>` block at the bottom of the main doc
- Establishing a new `docs/maintaining/` subtree for maintainer-facing docs
- Updating CODEOWNERS to mark the internal tooling and maintainer subtree as maintainer-only

---

## When to use this skill

Use this skill when:

1. You have **two things with overlapping names** or concepts in your product/codebase (e.g., "squad" = public GitHub-issue automation AND internal team-coordination layer).
2. **One is part of the product surface** (end users should know about it).
3. **One is internal tooling** (end users should never see it, but maintainers need to navigate it).
4. You want to **minimize end-user confusion** without hiding either thing entirely.

---

## How to apply this skill

### Step 1: Add a disambiguating one-liner to the public doc

In the existing bullet/section that names the product-facing concept, add a single clarifying sentence. Use an em-dash or parenthetical to signal it is a side note:

```markdown
- **Cloud-agent squad.** ... See [`docs/squad.md`](docs/squad.md). 
  _(Note: This is the GitHub issue management feature — not to be confused with the `.squad/` 
  directory, which is internal coordination tooling; see the maintainer area below.)_
```

**Why:** This acknowledges the existence of both without burying the explanation in a long parenthetical.

### Step 2: Create a collapsed maintainer-area `<details>` block

Place it at the very bottom of the main README (before or after the License section; your judgment):

```markdown
<details>
<summary>🛠️ Maintainer area — internal coordination tooling</summary>

Brief explanation of what the internal tooling is, who uses it, and where to find more info. Include:
- What it is (framework, coordination layer, etc.)
- Why it exists (team coordination, scaffolding internal processes)
- The naming collision acknowledgement (so readers understand why both exist)
- A pointer to the maintainer subtree for those who need more detail

</details>
```

**Key constraints:**
- **No `open` attribute** — must collapse by default so end users never see it on initial page render.
- **Under 200 words** — a pointer, not a manual.
- **Acknowledge the naming collision** — explain why both the product feature and the internal tool exist.

### Step 3: Create `docs/maintaining/` subtree

Create a new directory structure for maintainer-facing docs:

```
docs/
  maintaining/
    squad.md          (overview of the squad coordination layer)
    <future files>    (onboarding, runbooks, etc.)
```

Create an initial file (e.g., `docs/maintaining/squad.md`) that:
- Explains what the internal tooling is (with a link to the upstream source if it is open-source)
- Acknowledges the naming collision with the public surface
- Tours the key subdirectories in 200 words or less
- Lists the current standing directives / policies for that tooling
- Provides a pointer to key reference files (decision ledger, team roster, routing rules)

**Why a subtree:** Future maintainer docs have a natural home; you're not creating a one-off file, but a convention.

### Step 4: Update CODEOWNERS

Add entries for the internal tooling and the maintainer subtree:

```
# Squad coordination layer — maintainer-only tooling.
/.squad/                  @martinopedal
/docs/maintaining/        @martinopedal
```

Place this **after existing entries** (or in alphabetical order if your file uses that convention). Keep a **short descriptive comment** above the block.

---

## What NOT to do

1. **Do not remove or hide the product-facing concept** just to avoid naming confusion. If it is part of the product, it stays visible and documented.
2. **Do not use a `<details>` block with `open` attribute.** That defeats the purpose — maintainers will see it expanded, end users will scroll past it, and it clogs the page.
3. **Do not put detailed coordination details in the README one-liner.** Keep it one sentence; use the maintainer subtree for full explanation.
4. **Do not skip the CODEOWNERS update.** Without it, anyone can edit the internal tooling and maintainer docs, weakening the governance model.
5. **Do not name the maintainer subtree `docs/internal/` or similar.** Use `docs/maintaining/` to signal "for people who maintain this project," not "for internal use only."

---

## Example: Agentic ALZ (the case that birthed this skill)

| Element | Result |
| --- | --- |
| **Product concept** | "Cloud-agent squad" = GitHub issue automation for the Copilot agent. Documented in `docs/squad.md`. Stays visible in README. |
| **Internal tooling** | `.squad/` coordination layer (team charters, decisions, ceremonies). Documented in `docs/maintaining/squad.md`. Hidden behind collapsed `<details>` block. |
| **Disambiguator** | One-liner in README: "Note: This is the GitHub issue management feature — not to be confused with the `.squad/` directory, which is internal coordination tooling." |
| **CODEOWNERS** | Both `.squad/` and `docs/maintaining/` marked as maintainer-only (`@martinopedal`). |
| **Outcome** | End users read README, see the product feature, don't know `.squad/` exists. Maintainers expand the `<details>` block and find a pointer to full documentation. No confusion; no governance gaps. |

---

## Related patterns and skills

- **docs-always-updated** — if you create new maintainer docs in `docs/maintaining/`, they do NOT trigger the `docs/generated/` regeneration (they are not source-of-truth docs; they are prose). But if you edit schemas/prompts/policies/allowlists that are already documented, regenerate as usual.
- **CODEOWNERS extension** — any new path in CODEOWNERS should carry a short comment explaining its category.

---

## Checklist

When implementing this skill:

- [ ] Identified the two overlapping concepts (product surface + internal tooling).
- [ ] Added a one-line disambiguator to the existing public doc.
- [ ] Created a collapsed `<details>` block (no `open` attribute) at the bottom of the main doc.
- [ ] Created `docs/maintaining/<topic>.md` with a tour of the internal structure.
- [ ] Updated CODEOWNERS to mark both the internal tooling directory and `docs/maintaining/` as maintainer-only.
- [ ] Verified that the product-facing doc remains visible and unchanged (except for the one-liner).
- [ ] Verified that `gen_docs.py --check` still passes (maintainer docs are not auto-generated).

---

**End of skill doc.**
