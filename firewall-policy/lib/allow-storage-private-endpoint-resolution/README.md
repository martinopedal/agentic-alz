# `allow-storage-private-endpoint-resolution` — pre-approved RCG

Permits client subnets to resolve Private-Endpoint FQDNs (storage and
other Private-Link-fronted services) through the Azure-provided DNS via
the `AzurePlatformDNS` service tag on TCP+UDP/53. The actual data-plane
traffic to the storage Private Endpoint stays inside the VNet — this
rule covers the **DNS-only** flow.

## Inputs

| Variable | Type | Required | Description |
| --- | --- | :---: | --- |
| `firewall_policy_id` | string | ✓ | Resource id of the parent `azurerm_firewall_policy` (or child policy). |
| `priority` | number |   | RCG priority. Default `440`. |
| `client_source_ip_group_ids` | list(string) | ✓ | One or more `azurerm_ip_group` ids covering the client subnets. |
| `name` | string |   | RCG name. Default `allow-storage-private-endpoint-resolution`. |

## What is baked in

- Rule kind: **network**.
- Action: **Allow**.
- Destination: `AzurePlatformDNS` service tag — narrowest sanctioned
  form; no IP literals.
- Protocols/port: **TCP + UDP** on **53** only.

## What workloads can change

Only `firewall_policy_id`, `priority`, `client_source_ip_group_ids`, and
the RCG `name`.

## Verifying

```bash
conftest test --parser hcl2 \
  --policy policies \
  --namespace alz.firewall_rules \
  firewall-policy/lib/allow-storage-private-endpoint-resolution/main.tf
```

The corresponding typed RCG document is in [`rcg.json`](rcg.json) and
validates against
[`schemas/rcg.schema.json`](../../../schemas/rcg.schema.json).
