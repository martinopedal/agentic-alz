# Pre-approved RCG: Windows Update via Azure-curated WindowsUpdate FQDN tag.
#
# Sources: workload-supplied client IP groups (Windows VMs / VMSS that need
# OS patching).
# Destinations: the Azure-curated 'WindowsUpdate' FQDN tag — Microsoft
# maintains the underlying FQDN list, so the lib never enumerates raw
# Windows Update endpoints (which would drift).
# Protocols: HTTP/80 + HTTPS/443 (Windows Update needs both).
#
# Workloads parameterise this module via variables.tf; the rule body is
# fixed.

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
    name     = "allow-windows-update"
    priority = 100
    action   = "Allow"

    rule {
      name                  = "windows-update-fqdn-tag"
      source_ip_groups      = var.client_source_ip_group_ids
      destination_fqdn_tags = ["WindowsUpdate"]

      protocols {
        type = "Http"
        port = 80
      }
      protocols {
        type = "Https"
        port = 443
      }
    }
  }
}
