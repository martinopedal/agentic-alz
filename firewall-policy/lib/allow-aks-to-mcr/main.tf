# Pre-approved RCG: AKS nodes -> Microsoft Container Registry.
#
# Sources: workload-supplied AKS node IP groups.
# Destinations: mcr.microsoft.com and *.data.mcr.microsoft.com (single
# leftmost wildcard label, passes policies/firewall_rules.rego).
# Protocol: HTTPS/443 only.
#
# Workloads parameterise this module via variables.tf; the rule body itself
# is intentionally not configurable so NetSec can review the lib once and
# allow consumers to use it without further review.

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
    name     = "allow-aks-to-mcr"
    priority = 100
    action   = "Allow"

    rule {
      name              = "mcr-and-data-mcr"
      source_ip_groups  = var.aks_source_ip_group_ids
      destination_fqdns = [
        "mcr.microsoft.com",
        "*.data.mcr.microsoft.com",
      ]

      protocols {
        type = "Https"
        port = 443
      }
    }
  }
}
