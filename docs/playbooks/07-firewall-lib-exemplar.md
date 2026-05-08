# 07 — Firewall-lib exemplar

> Pre-approved Rule Collection Group (RCG) modules under
> `firewall-policy/lib/<pattern>/`. NetSec-CODEOWNED. The Composer LLM
> stage proposes PRs against the sibling `alz-firewall-policy` repo
> using these exemplars as the shape; this playbook governs in-repo
> exemplars only.

## Triggers

- Diff includes any file under `firewall-policy/lib/`.
- Diff includes any file under `firewall-policy/policies/base/` (when
  added).

## Steps

1. **One pattern per directory.** Each `firewall-policy/lib/<pattern>/`
   must contain exactly:
   - `main.tf` (or `main.bicep` once flavour-agnostic ships)
   - `variables.tf`
   - `README.md` describing the threat model and the use cases the
     pattern covers
   - `rcg.json` — typed Rule Collection Group document validated by
     `schemas/rcg.schema.json`.
2. **Schema first.** Author the `rcg.json` first; round-trip it through
   the orchestrator's RCG validator (`pytest
   orchestrator/tests/test_rcg_schema.py`). Wildcards are rejected by
   schema; do not work around this.
3. **Defence in depth.** `policies/firewall_rules.rego` must also pass
   against the pattern's `main.tf`. Schema and OPA together pin the
   safety boundary — both must hold.
4. **Naming and priority bands.** Follow the priority band convention
   established in existing patterns; document which band the pattern
   uses in `README.md`.
5. **No FQDN wildcards.** `*.example.com` collapses to "any" in
   practice. Schema enforces this; do not expand the regex.
6. **Composer compatibility.** The exemplar must be one the Composer
   prompt can imitate without inventing fields outside
   `schemas/rcg.schema.json`. If you find yourself wanting a field the
   schema does not provide, the schema change goes through
   `04-prompt-or-schema-change.md` first.

## Definition of Done

- [ ] `rcg.json` validates against `schemas/rcg.schema.json`.
- [ ] `ci / OPA policies (rego syntax + unit)` passes (the conftest
      step that runs `policies/firewall_rules.rego` against
      `firewall-policy/lib/*/main.tf` is the gate).
- [ ] `ci / orchestrator (lint + test)` passes (RCG schema test
      includes the new fixture).
- [ ] `ci / lint-instructions` passes.
- [ ] `rubberduck / check` passes.
- [ ] NetSec CODEOWNER approved.

## References

- *Azure Firewall — Rule processing logic* — Microsoft Learn.
  Retrieved 2026-05-08.
  <https://learn.microsoft.com/azure/firewall/rule-processing>
- *Azure Firewall Policy — rule collection groups* — Microsoft Learn.
  Retrieved 2026-05-08.
  <https://learn.microsoft.com/azure/firewall-manager/policy-overview>
- *NIST SP 800-41 Rev. 1 — Guidelines on Firewalls and Firewall Policy*.
  The threat-model framing this playbook borrows for `README.md`.
  Retrieved 2026-05-08.
  <https://csrc.nist.gov/publications/detail/sp/800-41/rev-1/final>
- `docs/threat-model.md` — the firewall surface's place in the overall
  threat model.
