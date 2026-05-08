# MCP server allowlist policy.
#
# Asserts the shape of `docs/mcp.allowlist.yaml`:
#   1. schema_version is "1".
#   2. Every server entry declares an id, transport, mode, and a non-empty
#      tools list.
#   3. mode is one of {"read", "write"}.
#   4. Any server with `mode: write` carries a `netsec_approval` block with
#      at minimum a `reviewer`, `date`, and `justification`.
#   5. The deliberately-excluded GitHub apply surface is not present in any
#      `github-mcp` entry's tools list — `github-mcp` MUST NOT be granted
#      tools that can push commits, edit workflow files, dispatch workflows,
#      bypass branch protection, or approve a deployment environment.
#
# Together with CODEOWNERS (`/docs/mcp.allowlist.yaml @netsec-team`) this
# means: a contributor can propose adding a server in `mode: write`, but the
# PR cannot merge without a NetSec reviewer signing off via the
# `netsec_approval` block AND via the CODEOWNER review.
#
# Conftest invocation (CI):
#   conftest test --parser yaml --policy policies \
#     --namespace alz.mcp_allowlist docs/mcp.allowlist.yaml

package alz.mcp_allowlist

import rego.v1

# ---------------------------------------------------------------------------
# Schema version.
# ---------------------------------------------------------------------------
deny contains msg if {
	input.schema_version != "1"
	msg := sprintf("mcp allowlist schema_version must be '1', got %q", [input.schema_version])
}

# ---------------------------------------------------------------------------
# Servers list must be present and non-empty.
# ---------------------------------------------------------------------------
deny contains msg if {
	not input.servers
	msg := "mcp allowlist must contain a 'servers' list"
}

deny contains msg if {
	count(input.servers) == 0
	msg := "mcp allowlist 'servers' list must be non-empty"
}

# ---------------------------------------------------------------------------
# Per-server shape checks.
# ---------------------------------------------------------------------------
deny contains msg if {
	some entry in input.servers
	not entry.id
	msg := sprintf("mcp server entry missing 'id': %v", [entry])
}

deny contains msg if {
	some entry in input.servers
	not entry.transport
	msg := sprintf("mcp server %q missing 'transport'", [entry.id])
}

deny contains msg if {
	some entry in input.servers
	not entry.mode
	msg := sprintf("mcp server %q missing 'mode'", [entry.id])
}

deny contains msg if {
	some entry in input.servers
	entry.mode
	not allowed_mode(entry.mode)
	msg := sprintf("mcp server %q has unknown mode %q (must be 'read' or 'write')", [entry.id, entry.mode])
}

deny contains msg if {
	some entry in input.servers
	not entry.tools
	msg := sprintf("mcp server %q missing 'tools' list", [entry.id])
}

deny contains msg if {
	some entry in input.servers
	entry.tools
	count(entry.tools) == 0
	msg := sprintf("mcp server %q must declare at least one tool", [entry.id])
}

allowed_mode("read")
allowed_mode("write")

# ---------------------------------------------------------------------------
# write-mode servers MUST carry a NetSec approval block.
# ---------------------------------------------------------------------------
deny contains msg if {
	some entry in input.servers
	entry.mode == "write"
	not entry.netsec_approval
	msg := sprintf(
		"mcp server %q declares mode='write' but has no netsec_approval block; this requires a NetSec CODEOWNER review",
		[entry.id],
	)
}

deny contains msg if {
	some entry in input.servers
	entry.mode == "write"
	entry.netsec_approval
	not entry.netsec_approval.reviewer
	msg := sprintf("mcp server %q netsec_approval missing 'reviewer'", [entry.id])
}

deny contains msg if {
	some entry in input.servers
	entry.mode == "write"
	entry.netsec_approval
	not entry.netsec_approval.date
	msg := sprintf("mcp server %q netsec_approval missing 'date'", [entry.id])
}

deny contains msg if {
	some entry in input.servers
	entry.mode == "write"
	entry.netsec_approval
	not entry.netsec_approval.justification
	msg := sprintf("mcp server %q netsec_approval missing 'justification'", [entry.id])
}

# ---------------------------------------------------------------------------
# Forbidden tools on github-mcp: anything that can mutate code, workflows,
# or environments. The PR/issue surface is the only sanctioned write path.
# ---------------------------------------------------------------------------
forbidden_github_tool_prefix := {
	"repos.create_or_update_file",
	"repos.delete_file",
	"git.create_commit",
	"git.update_ref",
	"actions.dispatch_workflow",
	"actions.create_workflow_dispatch",
	"environments.create_or_update",
	"environments.delete",
	"environments.approve_deployment",
	"branches.update_protection",
	"branches.delete_protection",
}

deny contains msg if {
	some entry in input.servers
	entry.id == "github-mcp"
	some tool in entry.tools
	tool in forbidden_github_tool_prefix
	msg := sprintf(
		"github-mcp tool %q is on the forbidden-apply-path list; github-mcp may not push commits, edit workflows, dispatch workflows, or approve environments",
		[tool],
	)
}
