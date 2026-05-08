# Outputs are written to the cross-state interface artifacts blob by a
# post-apply step in the orchestrator; they are NOT consumed via remote-state
# data sources by other repos.

output "intermediate_management_group_id" {
  description = "ALZ intermediate management group ID."
  value       = var.management_groups.intermediate_id
}

output "firewall_policy_id" {
  description = "Parent Azure Firewall Policy resource ID. Consumed by alz-firewall-policy/policies/base/."
  value       = try(module.firewall_policy.resource_id, null)
}

output "law_id" {
  description = "Log Analytics Workspace ID for diagnostic settings."
  value       = try(module.law.resource_id, null)
}

output "hub_vnet_id" {
  description = "Hub VNet ID. Consumed by spokes for peering."
  value       = try(module.hub_network.virtual_networks_resource_ids, null)
}

output "interface_storage_id" {
  description = "Storage account ID hosting interface artifacts."
  value       = try(module.interface_storage.resource_id, null)
}
