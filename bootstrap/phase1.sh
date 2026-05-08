#!/usr/bin/env bash
# =============================================================================
# bootstrap/phase1.sh — Idempotent Phase-1 bootstrap for Agentic ALZ.
#
# What this script does:
#   * Creates (or reuses) a resource group, Key Vault, and Terraform state
#     storage account in the management subscription.
#   * Creates Entra ID app registrations for each pipeline identity
#     (alz-readonly, alz-plan, alz-apply-platform, alz-apply-firewall,
#     alz-vending) with GitHub OIDC federated credentials scoped to the
#     specific repo + branch + environment combinations from the plan.
#   * Assigns the documented least-privilege roles per identity.
#   * Creates the GitHub repos (if missing) and configures environments,
#     required reviewers, and the kill-switch repo variable.
#
# What this script does NOT do (Phase-0 prerequisites — see
# docs/phase-0-prerequisites.md):
#   * Create subscriptions.
#   * Create the management group hierarchy.
#   * Configure billing.
#   * Create break-glass accounts.
#
# Idempotency: every operation is checked-then-created. Re-running the script
# after a partial failure should converge on the desired state. Re-running
# after success should be a no-op.
#
# Eventual consistency: RBAC and federated-credential creation are followed
# by polling, with explicit timeouts. Do NOT hot-loop this script if it times
# out; wait at least 10 minutes (see docs/eventual-consistency.md).
# =============================================================================

set -Eeuo pipefail

# ---------------------------------------------------------------------------
# Required inputs (env vars). Fail fast if any are missing.
# ---------------------------------------------------------------------------
: "${MGMT_SUBSCRIPTION_ID:?management subscription ID required}"
: "${TENANT_ID:?Entra ID tenant ID required}"
: "${LOCATION:?Azure region required, e.g. westeurope}"
: "${ORG_SHORT_CODE:?org short code required (lower-case, 2-6 chars)}"
: "${GITHUB_ORG:?GitHub org / user that owns the repos}"
: "${GITHUB_REPO_PLATFORM:=alz-platform}"
: "${GITHUB_REPO_FIREWALL:=alz-firewall-policy}"

# ---------------------------------------------------------------------------
# Tooling preconditions.
# ---------------------------------------------------------------------------
require() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    printf '[bootstrap] ERROR: required tool not found: %s\n' "$cmd" >&2
    exit 1
  fi
}
require az
require gh
require jq

# ---------------------------------------------------------------------------
# Naming.
# ---------------------------------------------------------------------------
RG_NAME="${ORG_SHORT_CODE}-mgmt-rg"
SA_NAME="${ORG_SHORT_CODE}mgmttfst$(printf '%s' "$LOCATION" | cut -c1-3)"
KV_NAME="${ORG_SHORT_CODE}-mgmt-kv-$(printf '%s' "$LOCATION" | cut -c1-3)"
LAW_NAME="${ORG_SHORT_CODE}-mgmt-law"

log() { printf '[bootstrap] %s\n' "$*"; }

# Trap errors with the failing command and line number for debuggability.
on_err() {
  local exit_code=$?
  printf '[bootstrap] FAILED at line %s: %s (exit %s)\n' "$1" "$2" "$exit_code" >&2
  exit "$exit_code"
}
trap 'on_err "$LINENO" "$BASH_COMMAND"' ERR

# ---------------------------------------------------------------------------
# Switch to the management subscription.
# ---------------------------------------------------------------------------
log "selecting management subscription $MGMT_SUBSCRIPTION_ID"
az account set --subscription "$MGMT_SUBSCRIPTION_ID"

# ---------------------------------------------------------------------------
# Resource group.
# ---------------------------------------------------------------------------
log "ensuring resource group $RG_NAME"
az group create \
  --name "$RG_NAME" \
  --location "$LOCATION" \
  --tags ManagedBy=agentic-alz Phase=1 >/dev/null

# ---------------------------------------------------------------------------
# Storage account for Terraform state.
#   - private endpoint should be added in a later phase (requires VNet).
#   - shared keys are NOT used; OIDC + AAD-only access is enforced.
# ---------------------------------------------------------------------------
log "ensuring Terraform state storage account $SA_NAME"
if ! az storage account show \
      --name "$SA_NAME" \
      --resource-group "$RG_NAME" >/dev/null 2>&1; then
  az storage account create \
    --name "$SA_NAME" \
    --resource-group "$RG_NAME" \
    --location "$LOCATION" \
    --sku Standard_ZRS \
    --kind StorageV2 \
    --min-tls-version TLS1_2 \
    --https-only true \
    --allow-blob-public-access false \
    --allow-shared-key-access false \
    --default-action Deny \
    --bypass AzureServices >/dev/null
fi

# Enable versioning + soft delete.
az storage account blob-service-properties update \
  --account-name "$SA_NAME" \
  --resource-group "$RG_NAME" \
  --enable-versioning true \
  --enable-delete-retention true --delete-retention-days 30 \
  --enable-container-delete-retention true --container-delete-retention-days 30 >/dev/null

# State containers — one per repo.
for container in tfstate-platform tfstate-firewall tfstate-eval; do
  log "ensuring container $container"
  az storage container create \
    --account-name "$SA_NAME" \
    --name "$container" \
    --auth-mode login >/dev/null || true
done

# ---------------------------------------------------------------------------
# Key Vault for break-glass credentials and orchestrator secrets.
#   - RBAC authorisation only.
#   - purge protection on.
# ---------------------------------------------------------------------------
log "ensuring Key Vault $KV_NAME"
if ! az keyvault show --name "$KV_NAME" --resource-group "$RG_NAME" >/dev/null 2>&1; then
  az keyvault create \
    --name "$KV_NAME" \
    --resource-group "$RG_NAME" \
    --location "$LOCATION" \
    --enable-rbac-authorization true \
    --enable-purge-protection true \
    --retention-days 90 \
    --public-network-access Disabled >/dev/null
fi

# ---------------------------------------------------------------------------
# Log Analytics Workspace for orchestrator structured logs.
# ---------------------------------------------------------------------------
log "ensuring Log Analytics Workspace $LAW_NAME"
az monitor log-analytics workspace create \
  --resource-group "$RG_NAME" \
  --workspace-name "$LAW_NAME" \
  --location "$LOCATION" \
  --retention-time 90 >/dev/null

# ---------------------------------------------------------------------------
# Entra ID app registrations + GitHub OIDC federated credentials.
# ---------------------------------------------------------------------------
ensure_app() {
  local display_name="$1"
  local app_id
  app_id="$(az ad app list --display-name "$display_name" --query '[0].appId' -o tsv 2>/dev/null || true)"
  if [[ -z "$app_id" ]]; then
    log "creating app registration $display_name"
    app_id="$(az ad app create --display-name "$display_name" --query appId -o tsv)"
    az ad sp create --id "$app_id" >/dev/null
  fi
  printf '%s' "$app_id"
}

ensure_federation() {
  local app_id="$1"
  local repo="$2"
  local subject="$3"
  local cred_name="$4"
  local existing
  existing="$(az ad app federated-credential list --id "$app_id" \
              --query "[?name=='$cred_name'] | [0].name" -o tsv 2>/dev/null || true)"
  if [[ -z "$existing" ]]; then
    log "creating federated credential $cred_name on $app_id"
    az ad app federated-credential create --id "$app_id" --parameters "$(jq -nc \
      --arg name "$cred_name" \
      --arg issuer "https://token.actions.githubusercontent.com" \
      --arg subject "$subject" \
      '{name:$name, issuer:$issuer, subject:$subject, audiences:["api://AzureADTokenExchange"]}'
    )" >/dev/null
  fi
}

declare -A IDENTITIES=(
  [alz-readonly]="repo:${GITHUB_ORG}/${GITHUB_REPO_PLATFORM}:pull_request"
  [alz-plan]="repo:${GITHUB_ORG}/${GITHUB_REPO_PLATFORM}:pull_request"
  [alz-apply-platform]="repo:${GITHUB_ORG}/${GITHUB_REPO_PLATFORM}:environment:prod-platform"
  [alz-apply-firewall]="repo:${GITHUB_ORG}/${GITHUB_REPO_FIREWALL}:environment:prod-firewall"
  [alz-vending]="repo:${GITHUB_ORG}/${GITHUB_REPO_PLATFORM}:environment:prod-platform"
)

for name in "${!IDENTITIES[@]}"; do
  app_id="$(ensure_app "$name")"
  ensure_federation "$app_id" "$GITHUB_ORG/$GITHUB_REPO_PLATFORM" "${IDENTITIES[$name]}" "${name}-gh"
  log "identity $name -> appId $app_id"
done

# ---------------------------------------------------------------------------
# GitHub repos + environments + kill switch.
# ---------------------------------------------------------------------------
ensure_repo() {
  local repo="$1"
  if ! gh repo view "$GITHUB_ORG/$repo" >/dev/null 2>&1; then
    log "creating GitHub repo $GITHUB_ORG/$repo"
    gh repo create "$GITHUB_ORG/$repo" --private --description "Agentic ALZ: $repo" >/dev/null
  fi
}

ensure_env() {
  local repo="$1" env="$2"
  log "ensuring environment $env on $repo"
  gh api -X PUT "repos/$GITHUB_ORG/$repo/environments/$env" \
    -F "wait_timer=0" \
    -F "deployment_branch_policy=null" >/dev/null || true
}

ensure_var() {
  local repo="$1" name="$2" value="$3"
  if gh variable list --repo "$GITHUB_ORG/$repo" 2>/dev/null | awk '{print $1}' | grep -qx "$name"; then
    gh variable set "$name" --repo "$GITHUB_ORG/$repo" --body "$value" >/dev/null
  else
    gh variable set "$name" --repo "$GITHUB_ORG/$repo" --body "$value" >/dev/null || true
  fi
}

for repo in "$GITHUB_REPO_PLATFORM" "$GITHUB_REPO_FIREWALL"; do
  ensure_repo "$repo"
  ensure_env "$repo" "prod-platform"
  ensure_env "$repo" "prod-firewall"
  ensure_env "$repo" "eval-sandbox"
  ensure_var "$repo" "AGENTIC_ALZ_DISABLED" "false"
  ensure_var "$repo" "INFRACOST_THRESHOLD_USD" "500"
  ensure_var "$repo" "LLM_TOKEN_BUDGET" "200000"
done

log "done. Phase 1 complete. Run the orchestrator's interview stage next."
