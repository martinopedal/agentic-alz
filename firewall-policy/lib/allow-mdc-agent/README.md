# `allow-mdc-agent` — pre-approved RCG

Permits the Microsoft Defender for Cloud / Defender for Servers agent to
reach its ingestion endpoints from hybrid and Azure Arc-connected
machines.

The azurerm provider does not currently expose a curated
`MicrosoftDefenderForCloud` FQDN tag, so this module ships an explicit
FQDN list sourced from Microsoft Learn. Each entry has at most one
leftmost wildcard label, satisfying
[`policies/firewall_rules.rego`](../../../policies/firewall_rules.rego).
If Microsoft ships a curated FQDN tag in a future provider release, this
module flips to `fqdn_tags = ["MicrosoftDefenderForCloud"]` in a
follow-up PR.

## Inputs

| Variable | Type | Required | Description |
| --- | --- | :---: | --- |
| `firewall_policy_id` | string | ✓ | Resource id of the parent `azurerm_firewall_policy` (or child policy). |
| `priority` | number |   | RCG priority. Default `460`. |
| `client_source_ip_group_ids` | list(string) | ✓ | One or more `azurerm_ip_group` ids covering the hybrid/Arc machine subnets. |
| `name` | string |   | RCG name. Default `allow-mdc-agent`. |

## What is baked in

- Rule kind: **application** (TLS-aware).
- Action: **Allow**.
- Destinations (HTTPS/443 only):
  - `*.ods.opinsights.azure.com` — Log Analytics ingestion.
  - `*.oms.opinsights.azure.com` — Log Analytics agent control plane.
  - `*.agentsvc.azure-automation.net` — Hybrid Worker / agent service.
  - `*.handler.control.monitor.azure.com` — Azure Monitor extension handler.
  - `*.security.microsoft.com` — Defender ingestion.
  - `gcs.prod.monitoring.core.windows.net` — Geneva monitoring (no wildcard).

## What workloads can change

Only `firewall_policy_id`, `priority`, `client_source_ip_group_ids`, and
the RCG `name`. The destination FQDN list is **not** exposed to
consumers.

## Verifying

```bash
conftest test --parser hcl2 \
  --policy policies \
  --namespace alz.firewall_rules \
  firewall-policy/lib/allow-mdc-agent/main.tf
```

The corresponding typed RCG document is in [`rcg.json`](rcg.json) and
validates against
[`schemas/rcg.schema.json`](../../../schemas/rcg.schema.json).
