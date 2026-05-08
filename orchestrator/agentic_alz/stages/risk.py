"""Risk classification stage.

Inputs: a ``terraform show -json`` plan dump and an Infracost diff JSON.
Output: a ``risk.json`` document matching ``schemas/risk.schema.json``.

The classifier is deterministic. It does not call any LLM. The score formula
is intentionally simple and auditable:

    score = (destroyed + replaced) * env_weight
          + max(infracost_delta_usd, 0) / 100
          + sum(flag_penalty for each flag set)

For v1 ``blocks_auto_apply`` is always ``True`` for platform-scope changes
because autonomous apply is a non-goal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..hashing import sha256_json

# Environment weighting from the consensus plan.
ENV_WEIGHTS: dict[str, int] = {
    "platform": 10,
    "workload": 1,
    "sandbox": 1,
}

# Per-flag score contribution; flags also drive the human-approval gates.
FLAG_PENALTIES: dict[str, int] = {
    "rbac": 25,
    "firewall": 25,
    "public-exposure": 25,
    "destructive": 20,
    "policy-assignment": 10,
    "key-vault-access": 15,
    "private-dns": 5,
    "data-deletion-risk": 30,
}

# Score at which a second reviewer is required.
SECOND_REVIEWER_THRESHOLD = 50


@dataclass(frozen=True)
class PlanCounts:
    """Counts of resource actions in a Terraform plan."""

    add: int
    change: int
    destroy: int
    replace: int


def count_actions(plan_json: dict[str, Any]) -> PlanCounts:
    """Count resource actions in a ``terraform show -json`` document.

    The Terraform JSON plan format encodes a "replace" as ``actions ==
    ["delete", "create"]`` (or the reverse). We treat any change containing
    both ``delete`` and ``create`` as a replace and exclude it from the
    delete and add tallies, matching the convention used by the human-
    readable plan summary.
    """
    add = change = destroy = replace = 0
    for rc in plan_json.get("resource_changes", []) or []:
        actions = list(rc.get("change", {}).get("actions", []) or [])
        if "delete" in actions and "create" in actions:
            replace += 1
        elif "create" in actions:
            add += 1
        elif "delete" in actions:
            destroy += 1
        elif "update" in actions:
            change += 1
        # "no-op" and "read" are intentionally ignored.
    return PlanCounts(add=add, change=change, destroy=destroy, replace=replace)


def detect_flags(plan_json: dict[str, Any]) -> list[str]:
    """Detect risk flags from a Terraform plan JSON.

    The detection is conservative: it errs on the side of flagging, on the
    theory that a false-positive flag causes an extra reviewer click while a
    false-negative could let an unsafe change through.
    """
    flags: set[str] = set()
    for rc in plan_json.get("resource_changes", []) or []:
        kind = rc.get("type", "")
        actions = set(rc.get("change", {}).get("actions", []) or [])
        after = rc.get("change", {}).get("after") or {}

        if "delete" in actions:
            flags.add("destructive")
            if kind in {"azurerm_storage_account", "azurerm_key_vault", "azurerm_sql_database"}:
                flags.add("data-deletion-risk")

        if kind == "azurerm_role_assignment" and actions & {"create", "update", "delete"}:
            flags.add("rbac")

        if kind in {
            "azurerm_firewall",
            "azurerm_firewall_policy",
            "azurerm_firewall_policy_rule_collection_group",
            "azurerm_firewall_network_rule_collection",
            "azurerm_firewall_application_rule_collection",
        } and actions & {"create", "update", "delete"}:
            flags.add("firewall")

        if kind == "azurerm_public_ip" and actions & {"create", "update"}:
            flags.add("public-exposure")
        if (
            isinstance(after, dict)
            and after.get("public_network_access_enabled") is True
            and actions & {"create", "update"}
        ):
            flags.add("public-exposure")

        if kind in {
            "azurerm_management_group_policy_assignment",
            "azurerm_subscription_policy_assignment",
            "azurerm_resource_group_policy_assignment",
            "azurerm_resource_policy_assignment",
        } and actions & {"create", "update", "delete"}:
            flags.add("policy-assignment")

        if kind in {"azurerm_key_vault_access_policy", "azurerm_role_assignment"} and (
            isinstance(after, dict)
            and "Key Vault" in str(after.get("scope", ""))
        ):
            flags.add("key-vault-access")

        if kind in {"azurerm_private_dns_zone", "azurerm_private_dns_zone_virtual_network_link"} and (
            actions & {"create", "update", "delete"}
        ):
            flags.add("private-dns")

    return sorted(flags)


def classify(
    plan_json: dict[str, Any],
    *,
    env: str,
    infracost_delta_usd: float = 0.0,
    summary_markdown: str | None = None,
) -> dict[str, Any]:
    """Build a typed risk report for the given plan.

    Args:
        plan_json: ``terraform show -json`` decoded.
        env: One of ``"sandbox"``, ``"platform"``, ``"workload"``.
        infracost_delta_usd: Monthly USD delta from Infracost.
        summary_markdown: Optional human summary to embed.

    Returns:
        A dict that validates against ``schemas/risk.schema.json``.
    """
    if env not in ENV_WEIGHTS:
        raise ValueError(f"unknown env {env!r}; expected one of {sorted(ENV_WEIGHTS)}")
    counts = count_actions(plan_json)
    flags = detect_flags(plan_json)
    weight = ENV_WEIGHTS[env]
    score = (
        (counts.destroy + counts.replace) * weight
        + max(infracost_delta_usd, 0.0) / 100.0
        + sum(FLAG_PENALTIES.get(f, 0) for f in flags)
    )
    return {
        "schema_version": "1",
        "plan_sha": sha256_json(plan_json),
        "score": round(score, 2),
        "weight": {"env": env, "value": weight},
        "counts": {
            "add": counts.add,
            "change": counts.change,
            "destroy": counts.destroy,
            "replace": counts.replace,
        },
        "infracost_delta_usd": round(float(infracost_delta_usd), 2),
        "flags": flags,
        "requires_second_reviewer": score >= SECOND_REVIEWER_THRESHOLD or bool(
            set(flags) & {"rbac", "firewall", "public-exposure", "data-deletion-risk"}
        ),
        # v1: autonomous apply is a non-goal at platform scope.
        "blocks_auto_apply": env == "platform",
        **({"summary_markdown": summary_markdown} if summary_markdown else {}),
    }
