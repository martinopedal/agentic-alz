# `allow-windows-update` — pre-approved RCG

Permits Windows VMs / VMSS to reach Windows Update via the Azure-curated
`WindowsUpdate` FQDN tag. Microsoft maintains the underlying FQDN list,
so the lib never enumerates raw Windows Update endpoints (which would
silently drift). Azure Firewall implicitly allows the protocols/ports
required by the FQDN tag.

## Inputs

| Variable | Type | Required | Description |
| --- | --- | :---: | --- |
| `firewall_policy_id` | string | ✓ | Resource id of the parent `azurerm_firewall_policy` (or child policy). |
| `priority` | number |   | RCG priority. Default `450`. |
| `client_source_ip_group_ids` | list(string) | ✓ | One or more `azurerm_ip_group` ids covering the Windows client subnets. |
| `name` | string |   | RCG name. Default `allow-windows-update`. |

## What is baked in

- Rule kind: **application**.
- Action: **Allow**.
- Destination: `WindowsUpdate` FQDN tag — Microsoft-curated; consumers
  cannot enumerate raw FQDNs through this lib.
- Protocols: HTTP/80 + HTTPS/443 (whatever the FQDN tag requires).

## What workloads can change

Only `firewall_policy_id`, `priority`, `client_source_ip_group_ids`, and
the RCG `name`.

## Verifying

```bash
conftest test --parser hcl2 \
  --policy policies \
  --namespace alz.firewall_rules \
  firewall-policy/lib/allow-windows-update/main.tf
```

The corresponding typed RCG document is in [`rcg.json`](rcg.json) and
validates against
[`schemas/rcg.schema.json`](../../../schemas/rcg.schema.json).
