### 2026-05-13T06:58:20Z: User directive — squad must be hidden from public-facing documentation
**By:** Martin (martinopedal) (via Copilot)

**What:**
Going forward, no `.squad/` information may surface in public-facing
documentation. The squad coordination layer (roster, charters, ceremonies,
casting, decisions, log/research) is **maintainer-only**. The only acknowledgement
in the public README must live inside a hidden / collapsed "Maintainer area"
section (e.g., GitHub `<details>` block) so end users do not see it by default.

This applies to:
- `README.md` — squad must be inside a collapsed `<details>` block (or equivalent
  hidden/maintainer section), not visible in the default rendered view.
- `docs/` — no docs page may link to or describe `.squad/` content for end users.
  If maintainer-facing docs about squad are needed, they live under
  `docs/maintaining/` (or equivalent maintainer subtree) and are linked ONLY
  from the hidden README section.
- `AGENTS.md` and `.github/copilot-instructions.md` — these are agent-instruction
  surfaces, not user-facing docs; they may continue to reference squad-relevant
  patterns where strictly necessary, but should NOT advertise the `.squad/`
  tree to end users either.
- `docs/generated/` — gen_docs.py must NOT emit `.squad/` content into any
  user-facing generated page.
- `docs/playbooks/` — playbooks may reference squad mechanics where they affect
  CI behavior, but should not lead an end-user reader to "go read `.squad/`".
- ROADMAP.md — already public; entries must not casually reference `.squad/`
  paths in a way that requires the reader to inspect them.

**Why:** End users / customers / external contributors of Agentic ALZ should
see a clean, focused product (deterministic GitOps pipeline + narrow LLM
stages). The squad coordination layer is internal tooling for the maintainer
(and squad itself); exposing it as a first-class surface dilutes the product
narrative and signals the wrong "shape" of the project to first-time readers.

**Implementation pattern:**

```markdown
<details>
<summary>🛠️ Maintainer area (squad coordination — internal tooling)</summary>

This repo uses [Squad](https://github.com/bradygaster/squad) — an in-repo
coordination layer for the AI maintenance team. The roster, charters,
decisions, and orchestration logs live under `.squad/` and are not part
of the Agentic ALZ product surface.

If you are a maintainer working with squad, see `docs/maintaining/squad.md`
(or equivalent). If you are an end user of Agentic ALZ, you can ignore
this section entirely.

</details>
```

**Counts as:** Standing directive (same shelf as "docs always updated" and
"SRE-as-stages, no SRE agent"). All future PRs that touch `README.md` or
public-facing docs must honor it. The Lead (Holden) and any agent editing
public docs must check this directive before promoting `.squad/` content.

**Captured for team memory; will route the README + maintainer-section work
to Holden after her current roadmap-greenlight task completes.**
