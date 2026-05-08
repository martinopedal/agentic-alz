# Pre-approved RCG: App Service -> Azure Key Vault via regional Service Tag.
#
# Sources: workload-supplied App Service IP groups.
# Destinations: AzureKeyVault.<region> service tag — narrowed to a single
# region to bound blast radius, never the global 'AzureKeyVault' tag.
# Protocol: TCP/443 only.
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

  network_rule_collection {
    name     = "allow-appservice-to-keyvault"
    priority = 100
    action   = "Allow"

    rule {
      name                  = "appservice-to-keyvault-regional"
      protocols             = ["TCP"]
      source_ip_groups      = var.appservice_source_ip_group_ids
      destination_addresses = ["AzureKeyVault.${var.region}"]
      destination_ports     = ["443"]
    }
  }
}
