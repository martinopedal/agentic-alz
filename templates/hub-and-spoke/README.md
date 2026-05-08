# Hub-and-spoke + Azure Firewall Premium — golden template (v1)

This directory is the **hand-built target** that the Generate stage produces.
It is intentionally not parameterised beyond what `inputs.yaml` requires; the
orchestrator overlays values onto it with deterministic rendering, not
template-engine cleverness.

> Status: **scaffolded skeleton.** The module wiring is correct in shape, but
> the values are placeholders. Before the first real apply, a platform
> engineer must:
>
> 1. Verify each AVM module version in `versions.lock` against the public
>    registry and the platform's compatibility matrix.
> 2. Fill in tenant-specific values via the orchestrator (do not hand-edit
>    `terraform.tfvars` here — Phase 2 generates it).
> 3. Configure the remote state backend in `backend.tf` to point at the
>    storage account created by `bootstrap/phase1.sh`.

## What this template deploys

- ALZ management group hierarchy (intermediate root + Platform / LandingZones
  / Decommissioned / Sandbox).
- Platform subscriptions placement under the hierarchy (assignment only;
  vending is out of scope).
- Connectivity hub VNet with subnets: `AzureFirewallSubnet`,
  `AzureFirewallManagementSubnet`, `GatewaySubnet`,
  `AzureBastionSubnet`, `PrivateResolverInbound`, `PrivateResolverOutbound`.
- Azure Firewall Premium with a parent firewall policy (federated mode).
- Log Analytics Workspace + diagnostic settings on the firewall, vnet, and
  storage account.
- Default route table for spokes pointing at the firewall private IP.
- Storage account hosting the cross-state interface artifacts blob.

## What this template does NOT deploy

- Workload spokes (those live in `alz-workloads/<name>/`).
- Firewall rule collections (those live in `alz-firewall-policy/`).
- Sentinel content, AKS, App Service, etc.
- Subscription creation (Phase 0 prerequisite).
