# `allow-aks-to-mcr` — pre-approved RCG

Permits AKS node egress to Microsoft Container Registry FQDNs over HTTPS.
This is one of the patterns called out in
[`firewall-policy/lib/README.md`](../README.md) and is the first concrete
lib RCG so consumers (and the future Firewall Composer / MCP importer)
have something real to reference.

## Inputs

| Variable | Type | Required | Description |
| --- | --- | :---: | --- |
| `firewall_policy_id` | string | ✓ | Resource id of the parent `azurerm_firewall_policy` (or child policy). |
| `priority` | number |   | RCG priority. Default `400`. |
| `aks_source_ip_group_ids` | list(string) | ✓ | One or more `azurerm_ip_group` ids covering the AKS node subnets. Workload-specific. |
| `name` | string |   | RCG name. Default `allow-aks-to-mcr`. |

## What is baked in

- Rule kind: **application** (TLS-aware).
- Action: **Allow**.
- Destinations: `mcr.microsoft.com`, `*.data.mcr.microsoft.com` (single
  leftmost wildcard label — passes
  [`policies/firewall_rules.rego`](../../../policies/firewall_rules.rego)).
- Protocol: HTTPS on 443.

## What workloads can change

Only `firewall_policy_id`, `priority`, `aks_source_ip_group_ids`, and the
RCG `name`. Sources, destinations, ports, and protocols are not exposed —
that is the whole point of the pre-approved library: consumers cannot
broaden the rule.

## Verifying

The rules in this module are designed to pass the firewall-rules OPA
policy. To check locally once Conftest is on PATH:

```bash
conftest test --parser hcl2 \
  --policy policies \
  --namespace alz.firewall_rules \
  firewall-policy/lib/allow-aks-to-mcr/main.tf
```

The corresponding typed RCG document (one of the things the future MCP
importer will produce) is in [`rcg.json`](rcg.json) — populated with a
**representative example** `source_ip_groups` value — and validates
against
[`schemas/rcg.schema.json`](../../../schemas/rcg.schema.json). At
deployment time, consumers of this Terraform module pass their real IP
group ids via the `aks_source_ip_group_ids` variable; the `rcg.json` is
a static fixture for the schema and not a runtime input.
