# Phase-1 bootstrap

`phase1.sh` is the **idempotent** bootstrap script. It assumes the
[Phase-0 prerequisites](../docs/phase-0-prerequisites.md) are already in
place — it cannot create subscriptions or grant tenant-level roles.

## Required environment

| Variable | Description |
| --- | --- |
| `MGMT_SUBSCRIPTION_ID` | Management subscription ID. |
| `TENANT_ID` | Entra ID tenant ID. |
| `LOCATION` | Primary Azure region (e.g. `westeurope`). |
| `ORG_SHORT_CODE` | 2–6 lower-case org code; embedded in resource names. |
| `GITHUB_ORG` | GitHub user/org owning the platform + firewall repos. |
| `GITHUB_REPO_PLATFORM` | Defaults to `alz-platform`. |
| `GITHUB_REPO_FIREWALL` | Defaults to `alz-firewall-policy`. |

## Required tooling

`az`, `gh`, `jq`. The script `require`s each at startup.

## What it creates

1. Resource group, Terraform-state storage account (versioned, soft-delete,
   AAD-only, shared-key disabled), Key Vault (RBAC-only, purge protection),
   Log Analytics Workspace.
2. Per-pipeline Entra ID app registrations (`alz-readonly`, `alz-plan`,
   `alz-apply-platform`, `alz-apply-firewall`, `alz-vending`) with GitHub
   OIDC federated credentials scoped to specific repo + branch + environment
   subjects.
3. GitHub repos (if missing), environments (`prod-platform`, `prod-firewall`,
   `eval-sandbox`), and the `AGENTIC_ALZ_DISABLED`, `INFRACOST_THRESHOLD_USD`,
   `LLM_TOKEN_BUDGET` repo variables.

## What it does NOT create

- Subscriptions (Phase 0).
- Management group hierarchy (Phase 0; the platform Terraform manages it
  thereafter via the AVM ALZ pattern module).
- Break-glass accounts (Phase 0).
- Branch protection rules (must be set in the GitHub UI for the first run;
  see the prerequisites doc).

## Re-running

The script is convergent: every operation is checked-then-created. On
transient Azure failures (especially RBAC propagation) it will exit with the
failing line and the failed command. Wait at least 10 minutes before
re-running, per [`eventual-consistency.md`](../docs/eventual-consistency.md).
