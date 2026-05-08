# Operational runbook

Audience: the on-call platform engineer for the management subscription.

## Daily checks

- [ ] Review the **drift** issues opened overnight (label: `drift`). Triage:
      classify each as expected (open a remediation PR), unexpected
      (investigate), or noise (close with reason).
- [ ] Review the **rbac-drift** issues (label: `rbac-drift`). Any change to
      Owner / User Access Administrator at platform scope requires immediate
      verification with the named principal.
- [ ] Skim the orchestrator's structured log dashboard for stages that
      exceeded their token budget or tool timeout.

## Weekly checks

- [ ] Review the **cost** report issue (label: `cost`). Investigate any
      anomaly above 25% week-on-week.
- [ ] Confirm the eval harness golden runs are still green. A red eval blocks
      all merges to `main`.
- [ ] Review pending firewall `lib/` PRs (sibling repo) with NetSec.

## On-demand: deploying a change

1. PR opened against `alz-platform/` (typically by Generate stage).
2. CI runs `validate`, `plan`, `policy-conformance`, `infracost`, `risk`.
3. Reviewer reads the **risk report** comment on the PR. If risk score >= 50
   *or* any of `rbac`, `firewall`, `public-exposure`, `destructive` flags are
   set, a second reviewer is required.
4. Merge to `main`.
5. `apply` workflow runs against the `prod-platform` environment; required
   reviewers approve in the GitHub UI.
6. Apply uses the **saved plan artifact** from the validate run; if the
   artifact is missing or older than 24 h the workflow refuses to run.
7. Post-apply, the workflow re-runs `terraform plan`. Non-empty diff opens an
   issue with label `post-apply-drift`.

## Emergency: kill switch

Set the repo variable `AGENTIC_ALZ_DISABLED=true`. All scheduled workflows
exit immediately on the first step. Triggered workflows refuse to run apply
jobs.

## Emergency: revert a bad apply

Terraform does not support automatic rollback. Procedure:

1. **Do not run `terraform state rm`.** Ever, without a Sev-1 incident open.
2. Identify the prior known-good commit on `alz-platform/`.
3. Open a revert PR. Let it go through the normal pipeline. The plan will
   show the inverse change.
4. If the bad apply created destructive changes (resource deletes), recovery
   is from backup, not from Terraform.

## Emergency: compromised OIDC identity

1. Set kill switch.
2. Disable the federated credential on the affected app registration in
   Entra ID.
3. Rotate by deleting and recreating the federated credential (re-run the
   relevant section of `bootstrap/phase1.sh`).
4. Audit all role assignments held by that identity in the last 30 days via
   Activity Log.
5. File an incident — see [`incident-response.md`](incident-response.md).

## State corruption

1. Set kill switch.
2. Storage account has versioning + soft delete. Restore the prior version of
   the affected `terraform.tfstate` blob via the portal. Document the
   timestamp restored to.
3. Run `terraform plan` from a clean clone. Compare to the last known plan in
   the validate workflow's artifact store.
4. Only then, lift the kill switch.
