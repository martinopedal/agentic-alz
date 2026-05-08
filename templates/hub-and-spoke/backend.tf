# Backend is configured by `terraform init -backend-config=...` from the
# orchestrator. The values come from the storage account created in
# bootstrap/phase1.sh and stored in the run's checkpoint blob.
terraform {
  backend "azurerm" {
    use_oidc = true
    use_azuread_auth = true
  }
}
