# Phase 0 — Manual prerequisites

These are the things a human with the appropriate Azure and GitHub roles must
do **before** `bootstrap/phase1.sh` can run successfully. They cannot be
automated by the orchestrator because creating them requires the very
permissions the orchestrator is being granted.

## Azure

- [ ] **Billing role.** EA Enrollment Account Owner *or* MCA Billing Profile
      Contributor on the billing scope where the management subscription will
      live. Required to create subscriptions.
- [ ] **Tenant-level role.** Entra ID Global Administrator *or* Privileged
      Role Administrator + Application Administrator. Required to create the
      app registrations and grant federated credentials.
- [ ] **Root management group.** Tenant root group enabled and the operator
      assigned `Management Group Contributor` at the root.
- [ ] **Resource provider registrations.** Register the following providers in
      the management subscription once it exists:
      `Microsoft.Management`, `Microsoft.Authorization`, `Microsoft.PolicyInsights`,
      `Microsoft.Network`, `Microsoft.Storage`, `Microsoft.KeyVault`,
      `Microsoft.OperationalInsights`, `Microsoft.Insights`, `Microsoft.Security`.
- [ ] **Sandbox subscription with spend cap.** Required for the eval harness.
      Spend cap must be enforced at the EA/MCA level (not by Cost Management
      alerts, which do not stop spend).
- [ ] **Break-glass accounts.** Two cloud-only Global Admin accounts with
      hardware FIDO2 keys, excluded from Conditional Access risk policies,
      monitored by sign-in alerting. **Never used by automation.**

## GitHub

- [ ] **Organization with Actions enabled** and OIDC trust policy permitting
      `token.actions.githubusercontent.com` as a federated issuer.
- [ ] **Branch protection on `main`** for this repo and the sibling repos:
      required reviews, required status checks (`validate`, `plan`,
      `policy-conformance`, `eval`), no force-push, signed commits required.
- [ ] **Environments:** `prod-platform`, `prod-firewall`, `eval-sandbox`.
      Each with required reviewers and (where appropriate) wait timers.
- [ ] **Repo variables:** `AGENTIC_ALZ_DISABLED` (kill switch — set to `true`
      to halt all scheduled runs), `INFRACOST_THRESHOLD_USD` (default `500`),
      `LLM_TOKEN_BUDGET` (default `200000`).
- [ ] **Repo secrets (only those needed):** `INFRACOST_API_KEY`. **No PATs.
      No Azure client secrets.** Azure auth is OIDC-only.

## Eventual-consistency awareness

Read [`eventual-consistency.md`](eventual-consistency.md). Several of the
prerequisites above (provider registration, RBAC propagation) take minutes
*after* the API call returns. The bootstrap script polls; do not rerun in a
hot loop if the first attempt times out — wait at least 10 minutes.

## Non-goals

The orchestrator does **not** take over creation of the billing scope, EA
enrollment, MCA agreement, custom domain federation, or any tenant-wide
identity governance. Those remain the operator's responsibility.
