# Library of pre-approved Rule Collection Groups

Workload repos reference these by exact path + pinned ref. Each lib RCG
satisfies a single, named pattern (e.g. `allow-aks-to-acr`). Adding a new
lib RCG requires one NetSec CODEOWNER approval; consuming an existing one
does not.

Conventions:

- One subdirectory per pattern: `lib/<pattern-name>/`.
- Each subdirectory contains `main.tf`, `variables.tf`, `README.md`.
- Variables describe **only** the workload-specific parameters (workload
  name, source IP groups, optional FQDN allowlist subset). Sources,
  destinations, ports, and protocols are baked in.
- Rules MUST pass `policies/firewall_rules.rego` (no wildcards beyond a
  single leftmost label, no `*` in port/protocol/destination).

## Initial v1 lib (shipped)

| Pattern | Kind | Destination | Protocol(s) |
| --- | --- | --- | --- |
| [`allow-aks-to-acr/`](allow-aks-to-acr/) | application | `<acr>.azurecr.io` + `<acr>.<region>.data.azurecr.io` (no wildcards) | HTTPS/443 |
| [`allow-aks-to-mcr/`](allow-aks-to-mcr/) | application | `mcr.microsoft.com`, `*.data.mcr.microsoft.com` | HTTPS/443 |
| [`allow-appservice-to-sql/`](allow-appservice-to-sql/) | network | `Sql.<region>` service tag (regional, never the global `Sql` tag) | TCP/1433 |
| [`allow-appservice-to-keyvault/`](allow-appservice-to-keyvault/) | network | `AzureKeyVault.<region>` service tag (regional) | TCP/443 |
| [`allow-storage-private-endpoint-resolution/`](allow-storage-private-endpoint-resolution/) | network | `AzurePlatformDNS` service tag (DNS-only) | TCP+UDP/53 |
| [`allow-windows-update/`](allow-windows-update/) | application | `WindowsUpdate` FQDN tag (Microsoft-curated) | HTTP/80 + HTTPS/443 |
| [`allow-mdc-agent/`](allow-mdc-agent/) | application | Documented MDC / Log Analytics / Azure Monitor FQDNs (single-leftmost wildcards only) | HTTPS/443 |

Each pattern's `rcg.json` is auto-validated against
[`schemas/rcg.schema.json`](../../schemas/rcg.schema.json) by
`orchestrator/tests/test_rcg_schema.py`, and each `main.tf` is
auto-validated against
[`policies/firewall_rules.rego`](../../policies/firewall_rules.rego)
by the `policies` job in `.github/workflows/ci.yml`.
