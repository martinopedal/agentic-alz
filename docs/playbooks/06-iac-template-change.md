# 06 — IaC template change (Terraform / Bicep)

> **Sensitive surface.** Any edit under `templates/` is one of the few
> paths that, at apply time, mutates Azure. AVM pinning, `versions.lock`
> round-trip, eventual-consistency landmines, and the multi-model judge
> all apply. Bicep is treated identically to Terraform once the
> Bicep-flavour roadmap items land; until then the Bicep notes below
> describe the *target* shape only.

## Triggers

- Diff includes any file under `templates/`.
- Diff includes `templates/**/versions.lock`.

## Pre-flight: this is sensitive

Cloud agents may be assigned only the narrow exemplars opted in by
`ROADMAP.md`. If you are an agent and you are not certain the issue
you were assigned is one of those, stop and unassign.

## Steps

1. **Pick the flavour from `inputs.yaml`** (when the Bicep roadmap items
   ship): `iac.flavour: terraform | bicep`. Mixing flavours within one
   workload is forbidden by schema; one workload = one flavour = one
   state / stack.
2. **AVM-only modules.** Every `module` block must use:
   - Terraform: `Azure/avm-(res|ptn)-*/azurerm` at exact semver.
   - Bicep (when shipped): `br/public:avm/(res|ptn)/...` at exact
     semver.
   No `ref=main`, no `~>`, no Git URLs. Enforced by
   `policies/avm_pinning.rego`.
3. **`versions.lock` round-trip.** Every module pinned in the template
   must appear in the matching `versions.lock` with byte-identical
   `source` + `version`. Add `approved_by` and `approved_on` for new
   entries.
4. **Eventual-consistency landmines.** Cross-reference
   `docs/eventual-consistency.md`. Anything that depends on a
   propagation delay (Graph API, RBAC role assignments, Diagnostic
   Settings) needs an explicit poll target documented.
5. **Plan deterministically.** A clean `terraform plan` (or
   `az deployment what-if`) on the unchanged inputs must produce zero
   diff after your change has been applied locally — re-runs are the
   eventual-consistency canary.
6. **Multi-model judge.** Templates are in the judge surface. Attach
   `judge-verdicts.json` from ≥ 2 distinct providers.
7. **Cost.** Run `infracost diff`; the rubberduck `## Blast radius`
   bullet must call out any new SKU or always-on PaaS.
8. **Apply path is unchanged.** Templates feed the immutable saved-plan
   artifact; this playbook never edits `apply.yml`.

## Definition of Done

- [ ] `validate / fmt` passes.
- [ ] `validate / tflint` passes.
- [ ] `validate / checkov` passes.
- [ ] `validate / conftest` passes (AVM pinning, naming, ALZ
      conformance, firewall rules).
- [ ] `validate / terraform-validate` passes.
- [ ] `ci / OPA policies (rego syntax + unit)` passes.
- [ ] `ci / lint-instructions` passes.
- [ ] `eval / offline` passes (golden plan diff reviewed and
      intentional).
- [ ] `judge-verdicts.json` from ≥ 2 providers attached to the PR.
- [ ] `rubberduck / check` passes; `## Blast radius` mentions any new
      SKU / always-on PaaS.

## References

- *Cloud Adoption Framework — Azure landing zones* — Microsoft Learn.
  Retrieved 2026-05-08.
  <https://learn.microsoft.com/azure/cloud-adoption-framework/ready/landing-zone/>
- *Azure Verified Modules — index* — Microsoft. The only sanctioned
  module source. Retrieved 2026-05-08.
  <https://azure.github.io/Azure-Verified-Modules/>
- *Terraform Registry — module versions* — HashiCorp. Why exact semver
  pinning matters for state determinism. Retrieved 2026-05-08.
  <https://developer.hashicorp.com/terraform/language/modules/sources>
- *Azure deployment stacks (Bicep)* — Microsoft Learn. The future Bicep
  flavour's drift / blast-radius semantics. Retrieved 2026-05-08.
  <https://learn.microsoft.com/azure/azure-resource-manager/bicep/deployment-stacks>
- `docs/eventual-consistency.md` — the inventory of landmines this
  playbook protects against.
