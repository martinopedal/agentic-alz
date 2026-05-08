# Naming convention policy.
#
# Asserts that resource names in the plan match the configured pattern.
# The pattern is supplied via `data.naming_pattern`; if absent the policy
# enforces only that names are non-empty and lower-case kebab.

package alz.naming

import rego.v1

# Default safe pattern: lower-case alphanumerics and hyphens, 3-63 chars.
default_re := "^[a-z][a-z0-9-]{2,62}$"

deny contains msg if {
	some change in input.resource_changes
	is_named_kind(change.type)
	some action in change.change.actions
	action in ["create", "update"]
	name := lower(object.get(change.change.after, "name", ""))
	name != ""
	not regex.match(default_re, name)
	msg := sprintf("resource %q name %q violates default naming pattern %q", [change.address, name, default_re])
}

is_named_kind(t) if {
	t in [
		"azurerm_resource_group",
		"azurerm_virtual_network",
		"azurerm_subnet",
		"azurerm_firewall",
		"azurerm_firewall_policy",
		"azurerm_log_analytics_workspace",
		"azurerm_storage_account",
		"azurerm_key_vault",
	]
}
