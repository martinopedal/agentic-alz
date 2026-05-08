# OPA / Conftest policies — ALZ conformance (v1)

These policies are the deterministic guardrails that gate every PR. They run
against:

- `terraform plan -json` output (resource-level checks),
- the rendered `main.tf` files (module pinning),
- the `versions.lock` manifest (allowlist integrity),
- the `firewall-policy/lib/` repo (rule-shape checks).

Run locally:

```bash
conftest test --policy policies templates/hub-and-spoke/main.tf
conftest test --policy policies plan.json
```

The `validate` GitHub workflow runs the same commands on every PR. Failures
block merge.

## Policy index

| File | Asserts |
| --- | --- |
| `avm_pinning.rego` | Every `module` block in `main.tf` uses an `Azure/avm-...` source pinned to an exact semver, and that source+version pair appears in `versions.lock`. |
| `alz_conformance.rego` | Plan does not introduce public IPs on the firewall management subnet, does not disable diagnostic settings on hub/firewall/storage, does not assign `Owner` outside known management groups, does not create resources in disallowed regions. |
| `firewall_rules.rego` | No rule with `*` in destination address, port, or protocol. No rule that widens an existing rule. (Applies in the firewall repo.) |
| `naming.rego` | Resource names match the configured pattern. |
