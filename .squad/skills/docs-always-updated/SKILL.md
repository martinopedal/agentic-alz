# SKILL: docs-always-updated

**Owner:** Alex (Eval & Test Engineer)  
**Created:** 2026-05-12  
**Pattern:** Generated docs freshness enforcement

---

## What this skill does

Ensures that generated documentation (under `docs/generated/`) stays byte-identical to what `scripts/gen_docs.py` would produce from source-of-truth files. This is a **deterministic pattern**, not an agentic one — the skill is a checklist and a script invocation, not a decision-making process.

---

## When to use this skill

**Always** when you edit any of:
- `schemas/*.schema.json`
- `prompts/*.md`
- `policies/*.rego`
- `docs/models.allowlist.yaml`
- `docs/mcp.allowlist.yaml`
- `docs/playbooks/*.md`
- `AGENTS.md` or `.github/copilot-instructions.md`
- `CODEOWNERS`
- `orchestrator/agentic_alz/cli.py`
- `scripts/squad_bootstrap.py`
- `ROADMAP.md`
- `decision/*/decision.json`

---

## How to apply this skill

### Step 1: Regenerate docs

After editing any source-of-truth file:

```bash
python scripts/gen_docs.py
```

This rewrites every file under `docs/generated/` to match the current sources.

### Step 2: Stage the regenerated files

```bash
git add docs/generated/
```

### Step 3: Commit both changes together

```bash
git commit -m "feat: update schema and regenerate docs"
```

**Important:** the source-of-truth change and the regenerated docs must land in the **same commit**. Do not commit the source change first and the docs later — the CI gate will fail on the first commit.

### Step 4: Verify the gate passes

The `docs / generate-and-check` job in `.github/workflows/docs.yml` runs `python scripts/gen_docs.py --check` and exits non-zero if any diff exists. If you followed steps 1-3, this check passes.

---

## What NOT to do

1. **Do not edit `docs/generated/` by hand.** Those files carry a "DO NOT EDIT BY HAND" banner. Edit the source and regenerate.
2. **Do not skip regeneration** and assume the CI will auto-fix it. The CI **blocks merge** if docs are stale; it does not auto-fix on PRs.
3. **Do not edit `scripts/gen_docs.py` without also updating `docs/generated/`**. The script is itself a source-of-truth file; the `docs.yml` workflow triggers on changes to it.

---

## Enforcement

### Primary gate (blocking)

**Job:** `docs / generate-and-check` in `.github/workflows/docs.yml`  
**Trigger:** PRs touching source-of-truth files  
**Action:** Runs `python scripts/gen_docs.py --check`; exits 1 if any diff exists; blocks merge.

### Safety net (advisory)

**Workflow:** `.github/workflows/regen-docs.yml` (proposed, not yet implemented)  
**Trigger:** Push to `main` with source-of-truth file changes  
**Action:** If `docs/generated/` is stale, opens a PR with the regenerated output. This is a safety net for force-merge/admin-override scenarios; normal flow is PR gate above.

---

## Related playbooks

- `03-doc-only.md` — if your change is **only** to markdown/comments and `docs/generated/` is untouched, this playbook applies; no regen needed.
- `04-prompt-or-schema-change.md` — editing prompts or schemas triggers the docs gate; you must regenerate.
- `05-policy-change.md` — editing policies triggers the docs gate; you must regenerate.
- `06-iac-template-change.md` — editing templates does **not** directly trigger the docs gate (templates are not a source-of-truth for `gen_docs.py`), but if you edit the template and also update a schema or policy, regenerate.

---

## Example workflow (agent perspective)

```markdown
## Task: Add a new `deployment_mode` enum to `schemas/inputs.schema.json`

1. Read `schemas/inputs.schema.json`.
2. Edit: add `"deployment_mode": {"type": "string", "enum": ["greenfield", "brownfield"]}`.
3. Run: `python scripts/gen_docs.py`.
4. Observe: `docs/generated/schemas.md` now includes the new enum.
5. Stage both changes: `git add schemas/inputs.schema.json docs/generated/schemas.md`.
6. Commit: `git commit -m "feat(schemas): add deployment_mode enum"`.
7. Push PR.
8. Verify: `docs / generate-and-check` passes.
```

---

## Checklist

Use this checklist in your PR's `## Definition of Done` section when applying this skill:

- [ ] I edited a source-of-truth file (schema, prompt, policy, allowlist, playbook, AGENTS.md, CODEOWNERS, cli.py, squad_bootstrap.py, ROADMAP.md, or decision.json).
- [ ] I ran `python scripts/gen_docs.py` (without `--check`).
- [ ] I staged the regenerated files with `git add docs/generated/`.
- [ ] I committed both changes (source + generated) in the same commit.
- [ ] `docs / generate-and-check` passes in CI.

---

## Coverage map (for reference)

| Source of truth | Generated doc | Renderer function |
| --- | --- | --- |
| `schemas/*.schema.json` | `docs/generated/schemas.md` | `render_schemas()` |
| `prompts/*.md` | `docs/generated/prompts.md` | `render_prompts()` |
| `policies/*.rego` | `docs/generated/policies.md` | `render_policies()` |
| `docs/models.allowlist.yaml` | `docs/generated/models.md` | `render_models()` |
| `docs/mcp.allowlist.yaml` | `docs/generated/mcp.md` | `render_mcp()` |
| `orchestrator/agentic_alz/cli.py` | `docs/generated/cli.md` | `render_cli()` |
| `ROADMAP.md` + `scripts/squad_bootstrap.py` | `docs/generated/roadmap.md` | `render_roadmap()` |
| `docs/playbooks/*.md` + `CODEOWNERS` | `docs/generated/playbooks-index.md` | `render_playbooks_index()` |
| `AGENTS.md` + `.github/copilot-instructions.md` + `prompts/system/agent-preamble.v1.md` | `docs/generated/agent-instructions-hash.md` | `render_agent_instructions_hash()` |
| `decision/*/decision.json` + `schemas/decision.schema.json` | `docs/generated/decisions-index.md` | `render_decisions_index()` |
| (index of the above) | `docs/generated/README.md` | `render_index()` |

---

**End of skill doc.**
