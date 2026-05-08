# Baseline rule collection groups

These RCGs are required for any ALZ to function. They are deployed once at
bootstrap, parented to the platform's parent firewall policy, and never
modified by workload PRs.

| RCG | What it allows |
| --- | --- |
| `azure_monitor.tf` | Egress to Azure Monitor data ingestion (`AzureMonitor` service tag, port 443). |
| `entra_id.tf` | Egress to Entra ID (`AzureActiveDirectory` service tag, ports 80/443). |
| `defender_for_cloud.tf` | Egress to Microsoft Defender for Cloud / MDC for endpoint backend. |
| `update_manager.tf` | Egress to Azure Update Manager and Windows Update FQDN tag. |
| `acr_aks_bootstrap.tf` | Egress required for AKS to bootstrap from a managed ACR (covered by FQDN tag where available). |
| `kms.tf` | Egress to Windows / SQL KMS endpoints. |
| `backup.tf` | Egress to Azure Backup service. |

The `.tf` files in this directory are placeholders in the scaffold. Each
should declare exactly one `azurerm_firewall_policy_rule_collection_group`
resource that is parented to the parent firewall policy ID exported from
the platform repo (consumed via the cross-state interface artifacts blob,
not via remote state data sources).
