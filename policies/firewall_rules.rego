# Firewall rules policy.
#
# Applies in the alz-firewall-policy repo (vendored here so the orchestrator
# can validate proposed lib/ patches before opening a PR). Runs against the
# `terraform plan -json` output for the firewall repo OR against parsed HCL of
# a proposed lib/ module.

package alz.firewall_rules

import rego.v1

# ---------------------------------------------------------------------------
# Wildcards in destination address, port, or protocol are forbidden.
# ---------------------------------------------------------------------------
deny contains msg if {
	some change in input.resource_changes
	change.type in [
		"azurerm_firewall_policy_rule_collection_group",
	]
	rcg := change.change.after
	some collection_kind in ["network_rule_collection", "application_rule_collection"]
	some collection in object.get(rcg, collection_kind, [])
	some rule in object.get(collection, "rule", [])
	some field in ["destination_addresses", "destination_ports", "protocols"]
	some value in object.get(rule, field, [])
	value == "*"
	msg := sprintf("rule %q in %q uses wildcard %q (forbidden)", [object.get(rule, "name", "?"), change.address, field])
}

# ---------------------------------------------------------------------------
# Destination FQDN wildcards may have at most one leftmost label.
# ---------------------------------------------------------------------------
deny contains msg if {
	some change in input.resource_changes
	change.type == "azurerm_firewall_policy_rule_collection_group"
	some collection in object.get(change.change.after, "application_rule_collection", [])
	some rule in object.get(collection, "rule", [])
	some fqdn in object.get(rule, "destination_fqdns", [])
	bad_wildcard(fqdn)
	msg := sprintf("rule %q uses overly broad FQDN wildcard %q", [object.get(rule, "name", "?"), fqdn])
}

bad_wildcard(fqdn) if {
	startswith(fqdn, "*.")
	rest := substring(fqdn, 2, -1)
	contains(rest, "*")
}

bad_wildcard(fqdn) if {
	fqdn == "*"
}
