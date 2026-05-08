# `allow-appservice-to-sql` — pre-approved RCG

Permits App Service egress to Azure SQL via the **regional** `Sql.<region>`
service tag on TCP/1433. Using the regional tag (rather than the global
`Sql` tag) bounds the blast radius to one Azure region, satisfying the
defence-in-depth posture required for the in-repo lib.

## Inputs

| Variable | Type | Required | Description |
| --- | --- | :---: | --- |
| `firewall_policy_id` | string | ✓ | Resource id of the parent `azurerm_firewall_policy` (or child policy). |
| `priority` | number |   | RCG priority. Default `420`. |
| `appservice_source_ip_group_ids` | list(string) | ✓ | One or more `azurerm_ip_group` ids covering the App Service VNet-integration subnets. |
| `region` | string | ✓ | Azure region short name; concatenated to the `Sql.` service tag (e.g. `westeurope` → `Sql.westeurope`). |
| `name` | string |   | RCG name. Default `allow-appservice-to-sql`. |

## What is baked in

- Rule kind: **network**.
- Action: **Allow**.
- Destination: `Sql.<region>` service tag — never the global `Sql` tag.
- Protocol/port: **TCP / 1433** only.

## What workloads can change

Only `firewall_policy_id`, `priority`, `appservice_source_ip_group_ids`,
`region`, and the RCG `name`. Protocol, port, and the destination shape
are not exposed.

## Verifying

```bash
conftest test --parser hcl2 \
  --policy policies \
  --namespace alz.firewall_rules \
  firewall-policy/lib/allow-appservice-to-sql/main.tf
```

The corresponding typed RCG document is in [`rcg.json`](rcg.json) and
validates against
[`schemas/rcg.schema.json`](../../../schemas/rcg.schema.json).
