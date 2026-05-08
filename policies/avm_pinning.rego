# AVM module pinning policy.
#
# Asserts that every `module` block in a Terraform configuration:
#   1. Uses a `source` from the Azure Verified Modules registry
#      (Azure/avm-{res,ptn}-*/azurerm).
#   2. Has an explicit `version` matching exact semver.
#   3. Appears in versions.lock with a matching version string.
#
# Input shape (Conftest's terraform parser, --parser hcl2 against main.tf):
#   input.module[name] = { "source": "...", "version": "..." }
#
# When the orchestrator runs this in CI it also passes versions.lock via
# `--data versions_lock=$(cat versions.lock)`.

package alz.avm_pinning

import rego.v1

# Lazy lookup of versions.lock from `data.versions_lock` when supplied; if
# not supplied the policy still checks shape but cannot cross-check membership.
allowlist := data.versions_lock.modules if data.versions_lock
else := []

# ---------------------------------------------------------------------------
# Deny any module with a missing source.
# ---------------------------------------------------------------------------
deny contains msg if {
	some name
	mod := input.module[name]
	not mod.source
	msg := sprintf("module %q has no source", [name])
}

# ---------------------------------------------------------------------------
# Deny any non-AVM source.
# ---------------------------------------------------------------------------
deny contains msg if {
	some name
	mod := input.module[name]
	mod.source
	not regex.match(`^Azure/avm-(res|ptn)-[a-z0-9-]+/azurerm$`, mod.source)
	msg := sprintf("module %q source %q is not an AVM module", [name, mod.source])
}

# ---------------------------------------------------------------------------
# Deny any missing or non-exact version.
# ---------------------------------------------------------------------------
deny contains msg if {
	some name
	mod := input.module[name]
	not mod.version
	msg := sprintf("module %q has no version", [name])
}

deny contains msg if {
	some name
	mod := input.module[name]
	mod.version
	not regex.match(`^[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9.-]+)?$`, mod.version)
	msg := sprintf("module %q version %q must be exact semver (no ranges, no 'main')", [name, mod.version])
}

# ---------------------------------------------------------------------------
# Deny any module not present in versions.lock (when allowlist is supplied).
# ---------------------------------------------------------------------------
deny contains msg if {
	count(allowlist) > 0
	some name
	mod := input.module[name]
	mod.source
	mod.version
	not allowlist_has(mod.source, mod.version)
	msg := sprintf("module %q (%s @ %s) is not in versions.lock", [name, mod.source, mod.version])
}

allowlist_has(source, version) if {
	some entry in allowlist
	entry.source == source
	entry.version == version
}
