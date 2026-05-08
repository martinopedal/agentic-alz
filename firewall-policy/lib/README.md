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

## Initial v1 lib (planned, not yet authored)

- `allow-aks-to-acr/` — AKS nodes → managed ACR pulls.
- `allow-aks-to-mcr/` — AKS nodes → Microsoft Container Registry FQDNs.
- `allow-appservice-to-sql/` — App Service → Azure SQL via Service Tag + port 1433.
- `allow-appservice-to-keyvault/` — App Service → Key Vault via Service Tag + 443.
- `allow-storage-private-endpoint-resolution/` — DNS-only flow for Private Link.
- `allow-windows-update/` — `WindowsUpdate` FQDN tag, 80/443.
- `allow-mdc-agent/` — MDC agent egress for hybrid/Arc machines.
