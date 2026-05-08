variable "firewall_policy_id" {
  type        = string
  description = "Resource id of the parent azurerm_firewall_policy or child policy this RCG attaches to."

  validation {
    condition     = can(regex("^/subscriptions/[0-9a-fA-F-]{36}/resourceGroups/[^/]+/providers/Microsoft.Network/firewallPolicies/[^/]+$", var.firewall_policy_id))
    error_message = "firewall_policy_id must be a fully qualified azurerm_firewall_policy resource id."
  }
}

variable "priority" {
  type        = number
  description = "RCG priority. Azure Firewall accepts 100-65000."
  default     = 430

  validation {
    condition     = var.priority >= 100 && var.priority <= 65000
    error_message = "priority must be between 100 and 65000."
  }
}

variable "appservice_source_ip_group_ids" {
  type        = list(string)
  description = "Resource ids of azurerm_ip_group resources covering the App Service VNet-integration subnets."

  validation {
    condition     = length(var.appservice_source_ip_group_ids) > 0
    error_message = "at least one source IP group must be supplied."
  }
}

variable "region" {
  type        = string
  description = "Azure region short name used to build the regional AzureKeyVault service tag (e.g. 'westeurope' -> 'AzureKeyVault.westeurope')."

  validation {
    condition     = can(regex("^[a-z]{2,}[a-z0-9]*$", var.region))
    error_message = "region must be the short Azure region name (lowercase, e.g. 'westeurope')."
  }
}

variable "name" {
  type        = string
  description = "RCG name. Lowercase kebab-case, 3-63 chars."
  default     = "allow-appservice-to-keyvault"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,61}[a-z0-9]$", var.name))
    error_message = "name must match ^[a-z][a-z0-9-]{1,61}[a-z0-9]$."
  }
}
