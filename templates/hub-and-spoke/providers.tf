terraform {
  required_version = "~> 1.9"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.10"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.platform_subscriptions.management.subscription_id
  use_oidc        = true
}

provider "azurerm" {
  alias           = "connectivity"
  features {}
  subscription_id = var.platform_subscriptions.connectivity.subscription_id
  use_oidc        = true
}

provider "azurerm" {
  alias           = "identity"
  features {}
  subscription_id = var.platform_subscriptions.identity.subscription_id
  use_oidc        = true
}
