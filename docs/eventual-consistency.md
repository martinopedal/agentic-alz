# Eventual-consistency landmines

Azure control-plane operations frequently return `200 OK` long before the
change is observable everywhere. The orchestrator MUST encode explicit waits
or polling for the cases below. Hot-looping these will produce false failures
and, worse, attempted "remediation" of phantom drift.

| Landmine | Typical lag | Required mitigation |
| --- | ---: | --- |
| RBAC role assignment propagation | 30–300 s, occasionally 30 min | Poll `azure-mcp` for the assignment to be visible to the *target* identity, not just the writer; retry with exponential backoff up to 30 min. |
| Management group hierarchy change | 60–600 s | Poll `Get-ManagementGroup` for the new parent before assigning policies. |
| Policy assignment effect (Audit/Deny) | 5–30 min | Do not rely on policy compliance state in the first 30 min after assignment. |
| `DeployIfNotExists` policy remediation | 30 min – several hours | Treat resources created by DINE as not-yet-present in Terraform state for at least one hour after assignment. |
| Subscription vending (alias create) | 60–600 s | Poll for `subscriptionId` on the alias resource, then poll the subscription's `state` until `Enabled`. |
| Resource provider registration | 5–60 min | Register up-front in Phase 0; verify state before plan. |
| Azure Firewall policy association | 60–300 s | After associating a policy to a firewall, wait for the firewall's `provisioningState` to return to `Succeeded` before applying rule changes. |
| Private DNS zone link propagation | 60–300 s | Wait before resolving names that depend on the link. |
| Key Vault soft-delete name reuse | up to 90 d | Use unique names; do not reuse purged-name in the same retention window. |
| Storage account name DNS propagation | 30–600 s | Tolerate `404` from blob endpoint immediately after creation. |
| Entra ID app credential propagation | 60–300 s | After `az ad app federated-credential create`, the first OIDC exchange may fail; retry with backoff. |

## Codification

- The orchestrator's `wait_for` helper (`orchestrator/agentic_alz/azure/waits.py`)
  exposes one function per landmine above with the documented backoff.
- CI jobs that poll Azure must use that helper, not raw `sleep`.
- Drift detection MUST suppress findings for resources whose owning policy
  assignment is younger than the documented lag (see `drift_cooldown.py`).

## Post-apply cooldown

After any successful `terraform apply`, drift detection for the affected state
file is suppressed for **2 hours**. This prevents the well-known loop where
the apply itself is detected as drift on the next nightly run.
