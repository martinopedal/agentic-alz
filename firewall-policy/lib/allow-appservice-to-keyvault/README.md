# `allow-appservice-to-keyvault` — pre-approved RCG

Permits App Service egress to Azure Key Vault via the **regional**
`AzureKeyVault.<region>` service tag on TCP/443. Using the regional tag
(rather than the global `AzureKeyVault` tag) bounds the blast radius to
one Azure region.

## Inputs

| Variable | Type | Required | Description |
| --- | --- | :---: | --- |
| `firewall_policy_id` | string | ✓ | Resource id of the parent `azurerm_firewall_policy` (or child policy). |
| `priority` | number |   | RCG priority. Default `430`. |
| `appservice_source_ip_group_ids` | list(string) | ✓ | One or more `azurerm_ip_group` ids covering the App Service VNet-integration subnets. |
| `region` | string | ✓ | Azure region short name; concatenated to `AzureKeyVault.` (e.g. `westeurope` → `AzureKeyVault.westeurope`). |
| `name` | string |   | RCG name. Default `allow-appservice-to-keyvault`. |

## What is baked in

- Rule kind: **network**.
- Action: **Allow**.
- Destination: `AzureKeyVault.<region>` service tag — never the global
  `AzureKeyVault` tag.
- Protocol/port: **TCP / 443** only.

## What workloads can change

Only `firewall_policy_id`, `priority`, `appservice_source_ip_group_ids`,
`region`, and the RCG `name`.

## Verifying

```bash
conftest test --parser hcl2 \
  --policy policies \
  --namespace alz.firewall_rules \
  firewall-policy/lib/allow-appservice-to-keyvault/main.tf
```

The corresponding typed RCG document is in [`rcg.json`](rcg.json) and
validates against
[`schemas/rcg.schema.json`](../../../schemas/rcg.schema.json).
