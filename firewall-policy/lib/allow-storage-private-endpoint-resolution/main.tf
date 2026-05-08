# Pre-approved RCG: Private Link DNS resolution to AzurePlatformDNS.
#
# Sources: workload-supplied client IP groups (any subnet that needs to
# resolve Private-Endpoint FQDNs through the Azure-provided resolver).
# Destinations: AzurePlatformDNS service tag — the narrowest sanctioned
# form for client-side DNS to Azure-managed resolvers.
# Protocols/ports: TCP and UDP, port 53 only.
#
# This is intentionally a DNS-only flow; the actual data-plane traffic to
# the storage Private Endpoint stays inside the VNet and never traverses
# the firewall. Workloads parameterise via variables.tf; the rule body is
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

  network_rule_collection {
    name     = "allow-storage-private-endpoint-resolution"
    priority = 100
    action   = "Allow"

    rule {
      name                  = "dns-to-azure-platform-dns"
      protocols             = ["TCP", "UDP"]
      source_ip_groups      = var.client_source_ip_group_ids
      destination_addresses = ["AzurePlatformDNS"]
      destination_ports     = ["53"]
    }
  }
}
