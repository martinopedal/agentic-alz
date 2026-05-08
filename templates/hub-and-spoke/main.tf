# =============================================================================
# Hub-and-spoke + Azure Firewall Premium — golden template skeleton
#
# This file wires the AVM modules pinned in versions.lock. Module source/version
# strings are duplicated here intentionally so terraform init can resolve them;
# the OPA policy `policies/avm_pinning.rego` enforces that every entry matches
# versions.lock at validate time.
# =============================================================================

locals {
  base_tags = merge(
    var.tags.defaults,
    {
      ManagedBy = "agentic-alz"
      Topology  = "hub-and-spoke"
    },
  )

  # Naming token substitution (small subset; Generate stage may override).
  name_prefix = format("%s-plat-%s", var.org.short_code, var.regions.primary)
}

# ---------------------------------------------------------------------------
# Management group hierarchy + policy assignments via the ALZ pattern module.
# ---------------------------------------------------------------------------
module "alz" {
  source  = "Azure/avm-ptn-alz/azurerm"
  version = "0.11.1"

  # NOTE: The real ALZ pattern module accepts a richer set of inputs than this
  # skeleton wires; see its README and update during Phase 2 hand-build. This
  # block exists so terraform validate succeeds against the module signature.
  enable_telemetry = false

  # Placeholders — Generate stage overlays the real values:
  # root_management_group_id        = var.management_groups.root_id
  # intermediate_management_group_id = var.management_groups.intermediate_id
}

# ---------------------------------------------------------------------------
# Connectivity hub VNet + standard ALZ subnets.
# ---------------------------------------------------------------------------
module "hub_network" {
  source  = "Azure/avm-ptn-network-hubnetworking/azurerm"
  version = "0.5.0"
  providers = {
    azurerm = azurerm.connectivity
  }

  enable_telemetry = false

  # Placeholders — Generate stage overlays:
  # location          = var.regions.primary
  # resource_group_name = "${local.name_prefix}-conn-rg"
  # hub_virtual_networks = { ... }
}

# ---------------------------------------------------------------------------
# Azure Firewall Premium policy (parent, federated mode).
# ---------------------------------------------------------------------------
module "firewall_policy" {
  source  = "Azure/avm-res-network-firewallpolicy/azurerm"
  version = "0.3.3"
  providers = {
    azurerm = azurerm.connectivity
  }

  enable_telemetry = false

  # name                = "${local.name_prefix}-fwpol"
  # location            = var.regions.primary
  # resource_group_name = "${local.name_prefix}-conn-rg"
  # sku                 = var.connectivity.firewall.sku
  # dns = {
  #   proxy_enabled = var.connectivity.firewall.dns_proxy_enabled
  # }
  tags = local.base_tags
}

# ---------------------------------------------------------------------------
# Azure Firewall.
# ---------------------------------------------------------------------------
module "firewall" {
  source  = "Azure/avm-res-network-azurefirewall/azurerm"
  version = "0.3.1"
  providers = {
    azurerm = azurerm.connectivity
  }

  enable_telemetry = false

  # name                = "${local.name_prefix}-afw"
  # location            = var.regions.primary
  # resource_group_name = "${local.name_prefix}-conn-rg"
  # firewall_sku_tier   = var.connectivity.firewall.sku
  # firewall_policy_id  = module.firewall_policy.resource_id
  tags = local.base_tags
}

# ---------------------------------------------------------------------------
# Log Analytics Workspace.
# ---------------------------------------------------------------------------
module "law" {
  source  = "Azure/avm-res-operationalinsights-workspace/azurerm"
  version = "0.4.2"

  enable_telemetry = false

  # name                = "${local.name_prefix}-law"
  # location            = var.regions.primary
  # resource_group_name = "${local.name_prefix}-mgmt-rg"
  # log_analytics_workspace_retention_in_days = var.logging.law_retention_days
  tags = local.base_tags
}

# ---------------------------------------------------------------------------
# Cross-state interface artifacts blob (storage account).
# ---------------------------------------------------------------------------
module "interface_storage" {
  source  = "Azure/avm-res-storage-storageaccount/azurerm"
  version = "0.5.0"

  enable_telemetry = false

  # name                = replace("${local.name_prefix}iface", "-", "")
  # location            = var.regions.primary
  # resource_group_name = "${local.name_prefix}-mgmt-rg"
  # account_replication_type = "ZRS"
  # min_tls_version     = "TLS1_2"
  # public_network_access_enabled = false
  tags = local.base_tags
}
