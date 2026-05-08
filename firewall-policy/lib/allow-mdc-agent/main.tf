# Pre-approved RCG: Microsoft Defender for Cloud agent egress.
#
# Sources: workload-supplied client IP groups (hybrid/Arc-connected
# machines whose MDC agent needs to reach the MDC ingestion endpoints).
# Destinations: explicit FQDN list documented by Microsoft Learn for the
# Defender for Cloud / Defender for Servers agent. Each entry has at most
# one leftmost wildcard label, so policies/firewall_rules.rego is
# satisfied. The azurerm provider does not currently expose a curated
# 'MicrosoftDefenderForCloud' FQDN tag, so the explicit-list path is the
# v1 choice; if a curated tag ships, this module flips to fqdn_tags in a
# follow-up.
# Protocol: HTTPS/443 only.
#
# Workloads parameterise this module via variables.tf; the destination
# list is intentionally fixed so NetSec reviews the lib once.

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

resource "azurerm_firewall_policy_rule_collection_group" "this" {
  name               = var.name
  firewall_policy_id = var.firewall_policy_id
  priority           = var.priority

  application_rule_collection {
    name     = "allow-mdc-agent"
    priority = 100
    action   = "Allow"

    rule {
      name             = "mdc-agent-endpoints"
      source_ip_groups = var.client_source_ip_group_ids
      destination_fqdns = [
        "*.ods.opinsights.azure.com",
        "*.oms.opinsights.azure.com",
        "*.agentsvc.azure-automation.net",
        "*.handler.control.monitor.azure.com",
        "*.security.microsoft.com",
        "gcs.prod.monitoring.core.windows.net",
      ]

      protocols {
        type = "Https"
        port = 443
      }
    }
  }
}
