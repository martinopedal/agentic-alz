# Pre-approved RCG: AKS nodes -> managed Azure Container Registry pulls.
#
# Sources: workload-supplied AKS node IP groups.
# Destinations: <acr>.azurecr.io (control-plane FQDN) and
# <acr>.<region>.data.azurecr.io (regional data-plane FQDN). Both are
# constructed from variables so no wildcards are emitted; the ACR name and
# data-plane region are workload-specific but the rule shape is fixed.
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
    name     = "allow-aks-to-acr"
    priority = 100
    action   = "Allow"

    rule {
      name             = "acr-control-and-data-plane"
      source_ip_groups = var.aks_source_ip_group_ids
      destination_fqdns = [
        "${var.acr_name}.azurecr.io",
        "${var.acr_name}.${var.acr_data_region}.data.azurecr.io",
      ]

      protocols {
        type = "Https"
        port = 443
      }
    }
  }
}
