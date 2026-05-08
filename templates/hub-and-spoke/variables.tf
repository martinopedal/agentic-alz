variable "org" {
  description = "Organisation metadata."
  type = object({
    name       = string
    short_code = string
  })
  validation {
    condition     = can(regex("^[a-z][a-z0-9]{1,5}$", var.org.short_code))
    error_message = "org.short_code must match ^[a-z][a-z0-9]{1,5}$ to fit Azure naming length budgets."
  }
}

variable "tenant" {
  type = object({
    tenant_id = string
  })
}

variable "management_groups" {
  type = object({
    root_id         = string
    intermediate_id = string
  })
}

variable "platform_subscriptions" {
  type = object({
    management = object({
      subscription_id = string
      display_name    = optional(string)
    })
    connectivity = object({
      subscription_id = string
      display_name    = optional(string)
    })
    identity = object({
      subscription_id = string
      display_name    = optional(string)
    })
  })
}

variable "regions" {
  type = object({
    primary   = string
    secondary = optional(string)
  })
}

variable "connectivity" {
  type = object({
    topology          = string
    hub_address_space = list(string)
    firewall = object({
      sku               = string
      policy_mode       = string
      dns_proxy_enabled = optional(bool, true)
    })
  })
  validation {
    condition     = var.connectivity.topology == "hub-and-spoke"
    error_message = "This template only renders hub-and-spoke. vWAN is deferred to v1.1."
  }
  validation {
    condition     = contains(["Standard", "Premium"], var.connectivity.firewall.sku)
    error_message = "firewall.sku must be Standard or Premium."
  }
  validation {
    condition     = contains(["central", "federated"], var.connectivity.firewall.policy_mode)
    error_message = "firewall.policy_mode must be central or federated."
  }
}

variable "logging" {
  type = object({
    law_retention_days = number
    sentinel_enabled   = optional(bool, false)
  })
  validation {
    condition     = var.logging.law_retention_days >= 30 && var.logging.law_retention_days <= 730
    error_message = "law_retention_days must be between 30 and 730."
  }
}

variable "policy_baseline" {
  type = object({
    set    = string
    deltas = optional(list(object({
      assignment    = string
      action        = string
      justification = optional(string)
    })), [])
  })
  validation {
    condition     = var.policy_baseline.set == "alz-default"
    error_message = "Only the alz-default policy set is supported in v1."
  }
}

variable "naming" {
  type = object({
    pattern = string
  })
}

variable "tags" {
  type = object({
    required = list(string)
    defaults = optional(map(string), {})
  })
}
