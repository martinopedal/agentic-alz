# `allow-aks-to-acr` — pre-approved RCG

Permits AKS node egress to a single managed Azure Container Registry
(control plane + regional data plane) over HTTPS. This is the second of
the patterns called out in
[`firewall-policy/lib/README.md`](../README.md).

## Inputs

| Variable | Type | Required | Description |
| --- | --- | :---: | --- |
| `firewall_policy_id` | string | ✓ | Resource id of the parent `azurerm_firewall_policy` (or child policy). |
| `priority` | number |   | RCG priority. Default `410`. |
| `aks_source_ip_group_ids` | list(string) | ✓ | One or more `azurerm_ip_group` ids covering the AKS node subnets. Workload-specific. |
| `acr_name` | string | ✓ | Short ACR name (the `<acr>` in `<acr>.azurecr.io`). |
| `acr_data_region` | string | ✓ | Azure region short name for the regional data-plane FQDN (e.g. `westeurope`). |
| `name` | string |   | RCG name. Default `allow-aks-to-acr`. |

## What is baked in

- Rule kind: **application** (TLS-aware).
- Action: **Allow**.
- Destinations: `<acr>.azurecr.io` and `<acr>.<region>.data.azurecr.io`,
  both fully qualified — **no wildcards**.
- Protocol: HTTPS on 443.

## What workloads can change

Only `firewall_policy_id`, `priority`, `aks_source_ip_group_ids`, the
ACR identity (`acr_name`, `acr_data_region`), and the RCG `name`. The
rule shape, action, and protocol are not exposed — that is the whole
point of the pre-approved library: consumers cannot broaden the rule.

## Verifying

```bash
conftest test --parser hcl2 \
  --policy policies \
  --namespace alz.firewall_rules \
  firewall-policy/lib/allow-aks-to-acr/main.tf
```

The corresponding typed RCG document is in [`rcg.json`](rcg.json) —
populated with a representative dummy `source_ip_groups` value and a
sample `acr_name` / region — and validates against
[`schemas/rcg.schema.json`](../../../schemas/rcg.schema.json). At
deployment time, consumers of this Terraform module pass their real IP
group ids and ACR identity via the variables; `rcg.json` is a static
fixture for the schema and not a runtime input.
