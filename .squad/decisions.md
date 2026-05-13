# Team Decisions

Append-only ledger. Squad (Coordinator) merges entries from `.squad/decisions/inbox/` after each batch.

### 2026-05-12T22:36:05Z: Squad initialized

**By:** martinopedal (via Squad init)
**What:** Cast 5-member squad from The Expanse universe (Holden, Naomi, Amos, Bobbie, Alex) plus exempt members Scribe and Ralph. AGENTS.md (root) remains the canonical agent-instruction surface; squad decisions extend it, never override.
**Why:** Bootstrap the orchestration layer for Agentic ALZ.

---

### 2026-05-12T22:36:05Z: User directive — docs always updated

**By:** martinopedal (via Squad coordinator)
**What:** Generated docs (`docs/generated/**`) and any agent-derived documentation MUST be kept in sync with source-of-truth files at all times. This is a standing rule, not a one-off.
**Why:** User request — captured for team memory. Implementation: every agent that touches a source-of-truth file (schemas, prompts, allowlists, CLI surface) must regenerate the corresponding generated doc in the same PR; Coordinator should treat doc-drift as a blocking concern, not a follow-up.

---

### 2026-05-12: "Docs always updated" enforcement pattern

**By:** Alex (Eval & Test Engineer)  
**What:** Two-tier enforcement for generated docs freshness: (1) PR gate blocks merge if `gen_docs.py --check` detects drift, (2) auto-regen workflow on push to `main` self-heals by opening a PR if drift slips through.  
**Why:** User directive requires docs always updated. Blocking check is primary enforcement; auto-regen is safety net for force-merge/admin-override/CI-bug scenarios.

**Pattern summary:**
- Tier 1 (PR gate, blocking, existing): `.github/workflows/docs.yml` → `docs / generate-and-check` job runs `python scripts/gen_docs.py --check` and fails if any diff exists.
- Tier 2 (auto-regen on push, advisory, new): `.github/workflows/regen-docs.yml` detects drift on `main` and opens a bot-authored PR (human-review-required, never auto-merge).
- Tier 3 (agent inline responsibility): Every agent that touches source-of-truth regenerates `docs/generated/` in same PR. Playbook DoD bullets enforce this.
- Coverage gap detection: New CI job fails if prompt lacks golden case exercise.
- What stays deterministic: `gen_docs.py`, `docs.yml`, `evals/replay.py`, `judge.py`, OPA policies, schemas, allowlists.

**Implementation priority:** Tier 1 enhancements (playbook DoD bullets) + coverage-gap-detection (immediate). Tier 2 (regen-docs.yml) when martinopedal confirms the pattern.

---

### 2026-05-12T23:21:00Z: SRE Agent Recommendation — skip for v1

**By:** Bobbie (Security Engineer, NetSec CODEOWNER)
**What:** Skip dedicated SRE agent in v1. Instead, add SRE-shaped automation as incremental deterministic stages (`postmortem_draft.py`, `compliance_snapshot.py`, `patch_triage.py`) owned by existing squad members.
**Why:** 13 traditional SRE concerns map to 7 GOOD FIT (narrow, read-only/advisory), 5 RISKY (judgment-heavy, context-dependent), 1 OUT-OF-SCOPE. Dedicated SRE agent would expand LLM surface beyond consensus plan's "narrow LLM stages in deterministic pipeline" philosophy without delivering sufficient bounded value.

**SRE concern fit map:**
- GOOD FIT (7): Postmortem drafting, runbook synthesis, capacity planning, cost anomaly detection, compliance evidence collection, patch triage, privileged access review
- RISKY (5): Incident triage, alert deduplication, security alert triage, threat modeling, resource decommissioning
- OUT-OF-SCOPE (1): SLO/SLI definition (workload-level)

**NetSec automation candidates:** Firewall conflict detection, suspect-rule scanner, effective-route summarization, rule usage analytics, Azure Policy remediation tasks, sandbox auto-approval, RBAC/firewall proposals.

**What we lose:** Postmortem velocity (5 days manual → 5 hours LLM-assisted), compliance audit prep speed, proactive capacity signals — all valuable but not v1-critical.

---

### 2026-05-13: Agentic Feature Roadmap — 10-item Phase 3 proposal

**By:** Holden (Lead)
**What:** Adopt a 10-item prioritized agentic feature roadmap for Phase 3, with explicit owner assignments. Consolidates 28+ candidates from 4 independent agent research streams.
**Why:** User asked: "What other features like policy can be automated? Should SRE agent play a part? How do we make it as agentic as possible?" Four agents researched independently; synthesis produces a coherent roadmap within guardrails.

**Ranked roadmap with owner assignments:**
1. Plan Summarizer (Amos) - Plan stage, advisory LLM prose on plan PRs
2. Rubberduck Generator (Alex) - Plan stage, auto-populate PR template sections
3. AVM Version-Bump (Amos) - Day-2, weekly cron opens version-bump PRs
4. Drift Triage (Holden) - Day-2, fill skeleton with agentic triage
5. Cost Guardrails (Amos) - Plan stage, threshold-based policy gates
6. ALZ Conformance Explainer (Alex) - Plan stage, OPA denial → CAF docs mapping
7. Shared PR Opener (Naomi) - Cross-cut, reusable advisory-PR primitive
8. Rego Unit-Test Generation (Bobbie) - Plan stage, LLM-assisted policy test synthesis
9. Cost Advisor (Amos) - Plan stage, cost anomaly detection + advisory
10. Compliance Snapshot (Bobbie) - Day-2, monthly evidence collection for auditors

**Supporting items (infrastructure, not ranked):**
- regen-docs.yml safety net (Alex)
- coverage-gap-detection job (Alex)
- firewall-conflicts.rego deterministic policy (Bobbie)

**Lifecycle map (finalized):** Bootstrap (human) → Interview/Design (agentic-CLI) → Plan (det-CI + agentic advisory) → Apply (det-CI, never agentic) → Day-2 (agentic-CI + CLI) → Decommission (human).

**SRE decision:** No SRE agent for v1. Re-evaluate if SRE-shaped stages reach ≥6 items.

**Docs decision:** Endorsed Alex's two-tier enforcement pattern. No docs-steward agent.

**Squad roster decision:** No changes for v1. Drummer (SRE), McManus (DevRel), MCP specialist all rejected.

**AGENTS.md changes required (separate PR, multi-model judge):**
- Add `evals/replay.py` and `orchestrator/agentic_alz/llm/judge.py` to "Things an agent must NEVER do" list.

**Key architectural insight:** Shared PR Opener (rank 7) is the critical enabler. Without it, M/L candidates each roll their own PR logic, fragmenting rubberduck/judge enforcement and complicating the roadmap execution.

---

### 2026-05-13T06:58:20Z: User directive — squad must be hidden from public-facing documentation

**By:** martinopedal (via Copilot CLI)  
**Status:** ACCEPTED-OPTION-A

**What:**
Going forward, no `.squad/` information may surface in public-facing documentation. The squad coordination layer (roster, charters, ceremonies, casting, decisions, log/research) is **maintainer-only**. The only acknowledgement in the public README must live inside a hidden / collapsed "Maintainer area" section so end users do not see it by default.

**Why:**
End users / customers / external contributors of Agentic ALZ should see a clean, focused product (deterministic GitOps pipeline + narrow LLM stages). The squad coordination layer is internal tooling for the maintainer (and squad itself); exposing it as a first-class surface dilutes the product narrative and signals the wrong "shape" of the project to first-time readers.

**Implementation pattern — Martin's directive (verbatim):**

> "Going forward, no `.squad/` information may surface in public-facing documentation. The squad coordination layer (roster, charters, ceremonies, casting, decisions, log/research) is **maintainer-only**. The only acknowledgement in the public README must live inside a hidden / collapsed "Maintainer area" section (e.g., GitHub `<details>` block) so end users do not see it by default."

**Visibility/privacy options considered:**

- **Option A (chosen):** Track `.squad/` in git; hide via README maintainer area + CODEOWNERS. Pros: Full auditability, CI-enforced sync, easy for contributors to discover. Cons: 7 new files in repo; maintains naming collision between public "Cloud-agent squad" and internal `.squad/` layer (requires clarification).
- **Option B:** Gitignore `.squad/` entirely. Pros: Invisible to public repo viewers. Cons: Lost auditability, no CI enforcement, harder for future maintainers to discover coordination layer on clone.
- **Option C (hybrid):** Track decisions/ and agents/ in git, gitignore log/. Pros: Partial auditability, smaller footprint. Cons: Fragmented; log discovery still a pain; harder to reason about completeness.
- **Option D:** Submodule `.squad/` to a private repo. Pros: Fully private, no naming collision in public repo tree. Cons: Clone complexity, dependency on separate private repo, breaks squad-cli convention (in-repo coordination).

**Rationale for Option A:**
Martin's choice optimizes for long-term maintainability: `.squad/` is tracked and auditable, the README honestly acknowledges it (with a collapsible section), and CODEOWNERS guards it from casual edits. The naming collision is resolved with a one-line clarifier in the README. Future squad members can discover the layer; external contributors don't stumble into it confused.

**Counts as:** Standing directive (same shelf as "docs always updated" and "SRE-as-stages, no SRE agent"). All future PRs that touch `README.md` or public-facing docs must honor it.

**Captured from:** .squad/decisions/inbox/copilot-directive-squad-hidden-from-public-docs.md  
**PR:** #28 (docs(maintainer): hide squad coordination layer behind README maintainer area)

---

### 2026-05-13T14:22:00Z: Roadmap greenlight — top 5 Phase 3 agentic features (re-ranked for gen_docs drift)

**By:** Holden (Lead), requested by martinopedal  
**Status:** ACCEPTED

**What:**
Greenlight 5 roadmap items for immediate ROADMAP.md upsert (ranks #1–5). Re-ranked from the synthesis baseline to promote regen-docs-backstop to #1 after the coordinator discovered active baseline drift on main during this work cycle (10 stale generated files, cp437 mojibake in cli.md).

**The 5 items (with original synthesis rank → final rank):**

1. **regen-docs-backstop** (was supporting/unranked → promoted to #1) — Active baseline drift on main (10 stale files, cp437 mojibake) directly violates the "docs always updated" standing directive; must fix before any other agentic feature ships.
2. **plan-summarizer** (was #1 → #2) — Cheapest high-impact agentic win: LLM prose on every plan PR replaces manual parsing of 800-line plan JSON.
3. **rubberduck-generator** (was #2 → #3) — Reduces rubberduck.yml check failures from ~30% to ~5% by auto-populating PR template sections.
4. **shared-pr-opener** (was #4 → #4) — Architectural enabler: without it, every M/L feature fragments rubberduck/judge enforcement.
5. **avm-version-bump** (was #5 → #5) — Automated dependency freshness catches AVM security patches within a week.

**Why:**
Five independent agents researched agentic feature candidates. Holden synthesized 28+ candidates into a 10-item prioritized roadmap. Martin asked: "greenlight the top 5 for ROADMAP.md upsert." During synthesis execution, the coordinator detected active docs drift — a violation of the standing "docs-always-updated" directive — and promoted regen-docs-backstop to #1. Remaining four items preserve the synthesis dependency order.

**Captured from:** .squad/decisions/inbox/holden-roadmap-greenlight-top5.md  
**PR:** #27 (chore(roadmap): greenlight top-5 Phase 3 agentic features)

**Self-extracted skill (Holden):** drift-to-roadmap-promotion — When evidence surfaces that a supporting-infrastructure item is actively breaking a standing directive, re-rank immediately and promote to high priority. The cost of fixing is asymmetric: gen_docs drift costs credibility + clogs future PRs; fixing it costs one focused sprint item.

---

### 2026-05-13T08:15:00Z: Implementation decision — hide squad behind README maintainer area (Option A)

**By:** Holden (Lead), implementing martinopedal's directive  
**Status:** ACCEPTED

**What:**
Full specification for PR-ready implementation of Martin's "squad-hidden-from-public-docs" directive, using Option A (track `.squad/`, hide via README + maintainer area + CODEOWNERS).

**Changes (3 file edits + 1 new file):**

1. **README.md edit:** Add one-line clarifier to existing "Cloud-agent squad" bullet (lines 73–80) to disambiguate from internal `.squad/` coordination layer.
2. **README.md new section:** Add collapsed `<details>` block before License section, explaining what `.squad/` is and pointing maintainers to docs/maintaining/squad.md.
3. **NEW:** docs/maintaining/squad.md — 300-word maintainer-facing overview of squad coordination layer, directory tour, standing directives, and references.
4. **CODEOWNERS:** Add two lines marking `.squad/` and `docs/maintaining/` as maintainer-only.

**Why:**
Martin's directive requires `.squad/` to be invisible to end users but auditable and discoverable for maintainers. README maintainer area + dedicated docs/maintaining/ subtree + CODEOWNERS guards achieve all three. No behavior change; pure documentation.

**Captured from:** .squad/decisions/inbox/holden-readme-hide-squad.md  
**PR:** #28 (docs(maintainer): hide squad coordination layer behind README maintainer area)

**Self-extracted skill (Holden):** hide-internal-tooling-behind-maintainer-area — When tooling is necessary but not part of the product surface, establish a convention: (1) collapsed README details block with disambiguation, (2) dedicated maintainer-facing docs subtree, (3) CODEOWNERS lock. This scales to future maintainer-only features without cluttering the public narrative.


---

### 2026-05-13T15:00:00Z: REVERSAL — squad is part of the agentic showcase, not hidden (supersedes squad-hidden-from-public-docs)

**By:** Coordinator (martinopedal-driven nudge)
**Status:** ACCEPTED — SUPERSEDES the 2026-05-13T06:58:20Z entry (squad-hidden-from-public-docs) AND the 2026-05-13T08:15:00Z entry (readme-hide-squad-implementation)

**What:**
`.squad/` stays VISIBLE in the public README and public-facing docs. The squad coordination layer is reframed as part of the cross-cutting agentic story this repo demonstrates, NOT internal tooling to hide. PR #28 (which implemented Option A: hide via maintainer area) is closed; a replacement PR #28b will:

1. Add a small section in the README that frames `.squad/` as cross-cutting agentic evidence (sits among the existing cross-cutting guarantees).
2. KEEP the disambiguating one-liner inside the existing "Cloud-agent squad" bullet (the two-meanings-of-squad clarification is still genuinely useful).
3. Move/rename `docs/maintaining/squad.md` (planned in PR #28) → `docs/squad-coordination.md` (public-facing coordination guide).
4. Drop the `docs/maintaining/` subtree entirely.
5. Keep CODEOWNERS entries for `/.squad/` and `/docs/squad-coordination.md` — visibility ≠ ungated edits; owner review still required.

**Why (martinopedal's nudge, paraphrased and accepted):**

> "in this repo, squad should perhaps be in the repo since it's an agentic focus? decide before we do anything"

Agentic ALZ's identity *is* "deterministic governance with narrow LLM stages, demonstrated on a production-bound Azure surface." Hiding the agentic coordination layer that built the repo is incongruent with that pitch. A knife company doesn't hide its knives.

**Reasoning (what the Coordinator weighed before reversing):**

1. **Eat your own dog food.** Visible `.squad/` is *evidence* this team uses agentic patterns to ship agentic features. That's credibility CSAs and security reviewers will weigh.
2. **Naming collision becomes a feature when both are visible.** "Cloud-agent squad" (product: ROADMAP → @copilot) AND `.squad/` (maintenance team coordination) showcase the same governance philosophy at two layers. Side-by-side they reinforce; hidden, they look like accidental clutter.
3. **Decision ledger and skill artifacts are *good* content.** `docs-always-updated`, `SRE-as-stages`, `drift-to-roadmap-promotion`, `multi-agent-synthesis`, `hide-internal-tooling-behind-maintainer-area`, this very reversal entry — educational artifacts, not embarrassing internals. They demonstrate sound judgment and build reviewer trust.
4. **A `<details>` "🛠️ Maintainer area" block draws MORE attention than inline visibility would.** Hiding-with-a-collapsed-block is the worst of both worlds: it's discoverable and weirdly framed.
5. **Risks weighed and rejected:** public sees prompt engineering (charters describe roles, not prompts; transparent governance is a feature); candid learnings expose internals (the learnings I've reviewed are marketing material, not warts); competitors copy patterns (coordination patterns aren't a moat — execution is); genuinely confidential content (handled case-by-case; don't put it in tracked files).

**Counts as:** Standing directive — replaces `squad-hidden-from-public-docs`. All future PRs that touch README.md or public-facing docs must honor *visibility*, not concealment, of `.squad/`.

**Captured from:** Coordinator session 2026-05-13 (greenlight cycle), post-PR-#28-CI-triage reversal turn. No inbox file — direct user nudge captured into ledger.

**PR:** #28 (CLOSED in favour of this reversal); PR #28b (forthcoming) will implement.

**Self-extracted skill (Coordinator):** reversal-without-rewriting-history — When a prior decision needs to be reversed: (1) leave the original entry intact (preserves audit trail), (2) add a new entry whose Status line explicitly names the entries it supersedes, (3) explain the nudge or evidence that triggered the reversal, (4) lay out the concrete consequences (what gets closed/rebuilt), (5) update the standing-directive shelf so downstream readers see the new rule first. Never edit the superseded entry — readers must be able to see the trajectory.

### 2026-05-13T16:30:00Z: graphql-replaceactorsforassignable-is-the-only-path-that-sticks

The four-PR debugging chain (#29 -> #30 -> #31 -> #38) found that:
- the Copilot bot's display name (`Copilot`) is not its API login;
- the real underlying login is `copilot-swe-agent` (verified via
  `repository.suggestedActors(capabilities:[CAN_BE_ASSIGNED])`);
- `POST /repos/{owner}/{repo}/issues` rejects the bot at creation time
  with HTTP 422 `cannot be assigned to this issue`;
- `POST /repos/{owner}/{repo}/issues/{n}/assignees` returns 200 OK with
  the bot login but **silently does NOT** add it to the assignees array;
- the only API path that actually sticks is the GraphQL
  `replaceActorsForAssignable` mutation against the bot's node ID
  (which is what the GitHub web UI uses internally).

PR #38 reworks `scripts/squad_bootstrap.py` to discover the bot node
ID at runtime via `suggestedActors` and to assign Copilot via the
GraphQL mutation in both CREATE and UPDATE paths. The REST
`add_assignees` helper is left in place for any future human-assignee
use case but is no longer the path the bootstrapper uses for Copilot.

