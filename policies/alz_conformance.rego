# ALZ conformance policy.
#
# Runs against `terraform show -json plan.tfplan` output (Conftest's `--parser
# json`). Asserts safety properties that must hold for any platform plan.

package alz.conformance

import rego.v1

# Denylist of regions for v1 (configurable via data.allowed_regions).
allowed_regions := data.allowed_regions if data.allowed_regions
else := [
	"westeurope",
	"northeurope",
	"norwayeast",
	"swedencentral",
	"uksouth",
	"eastus",
	"eastus2",
	"westus3",
]

planned := input.resource_changes if input.resource_changes
else := []

# ---------------------------------------------------------------------------
# No new public IPs attached to the firewall management subnet.
# ---------------------------------------------------------------------------
deny contains msg if {
	some change in planned
	change.type == "azurerm_public_ip"
	is_create_or_update(change.change.actions)
	contains_lower(json.marshal(change.change.after), "azurefirewallmanagementsubnet")
	msg := sprintf("public IP %q would be associated with AzureFirewallManagementSubnet", [change.address])
}

# ---------------------------------------------------------------------------
# Diagnostic settings on the firewall, hub VNet, and storage account must
# remain enabled. We treat any "delete" of `azurerm_monitor_diagnostic_setting`
# whose target is one of those resources as a denial.
# ---------------------------------------------------------------------------
deny contains msg if {
	some change in planned
	change.type == "azurerm_monitor_diagnostic_setting"
	"delete" in change.change.actions
	target := lower(object.get(change.change.before, "target_resource_id", ""))
	some keyword in ["firewall", "virtualnetwork", "storageaccount"]
	contains(target, keyword)
	msg := sprintf("diagnostic setting %q for %q would be deleted", [change.address, target])
}

# ---------------------------------------------------------------------------
# Owner role assignments are forbidden outside the platform management group.
# ---------------------------------------------------------------------------
deny contains msg if {
	some change in planned
	change.type == "azurerm_role_assignment"
	is_create_or_update(change.change.actions)
	role := lower(object.get(change.change.after, "role_definition_name", ""))
	role == "owner"
	scope := lower(object.get(change.change.after, "scope", ""))
	not contains(scope, "/managementgroups/")
	msg := sprintf("Owner role assignment %q targets non-management-group scope %q", [change.address, scope])
}

# ---------------------------------------------------------------------------
# Resources must be created in an allowed region.
# ---------------------------------------------------------------------------
deny contains msg if {
	some change in planned
	is_create_or_update(change.change.actions)
	loc := lower(object.get(change.change.after, "location", ""))
	loc != ""
	not loc in allowed_regions
	msg := sprintf("resource %q targets non-allowed region %q", [change.address, loc])
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
is_create_or_update(actions) if {
	some a in actions
	a in ["create", "update"]
}

contains_lower(s, needle) if {
	contains(lower(s), lower(needle))
}
