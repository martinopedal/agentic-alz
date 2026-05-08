"""Safety wrapper for the ``terraform`` CLI.

Goals:

* Keep destructive operations behind an explicit override flag.
* Force apply to consume an immutable saved plan artifact (never to plan
  + apply in one step).
* Honour the global kill switch.

This module deliberately contains *no* logic for invoking subprocesses in
production CI — that lives in ``.github/workflows/apply.yml``. What lives
here is the policy layer that classifies a Terraform CLI invocation as
permitted or denied, with a pure-Python implementation that the orchestrator
and a thin shim script both reuse.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ..killswitch import assert_enabled

# Subcommands that require an explicit override flag.
_DESTRUCTIVE_SUBCOMMANDS: frozenset[str] = frozenset(
    {
        "destroy",
        "force-unlock",
    }
)

# State subcommands that can corrupt or rewrite state.
_DANGEROUS_STATE_SUBCOMMANDS: frozenset[str] = frozenset(
    {
        "rm",
        "mv",
        "replace-provider",
        "push",
    }
)

# Apply-time flags the wrapper rejects to enforce "apply only a saved plan".
_FORBIDDEN_APPLY_FLAGS: frozenset[str] = frozenset(
    {
        "-auto-approve",
        "--auto-approve",
        "-destroy",
        "--destroy",
    }
)


class TerraformOperationDenied(PermissionError):
    """Raised when a Terraform CLI invocation violates v1 policy."""


@dataclass(frozen=True)
class Decision:
    """Outcome of policy evaluation for one Terraform CLI invocation."""

    allowed: bool
    reason: str


def evaluate(args: Sequence[str], *, override: bool = False) -> Decision:
    """Evaluate a Terraform CLI argv against v1 policy.

    Args:
        args: argv as passed to the ``terraform`` binary, **without** the
            program name (i.e. ``["plan", "-out", "tfplan"]``).
        override: When ``True``, destructive subcommands are permitted. The
            override is intended to be set only by an apply environment after
            human approval; it is never set by the orchestrator on its own.

    Returns:
        A :class:`Decision` whose ``allowed`` field tells the caller whether
        to proceed and whose ``reason`` is suitable for logging.
    """
    assert_enabled()  # propagates KillSwitchEngaged

    if not args:
        return Decision(False, "empty argv")
    sub = args[0]
    rest = list(args[1:])

    if sub in _DESTRUCTIVE_SUBCOMMANDS and not override:
        return Decision(
            False,
            f"subcommand {sub!r} is destructive; requires explicit override",
        )

    if sub == "state" and rest and rest[0] in _DANGEROUS_STATE_SUBCOMMANDS and not override:
        return Decision(
            False,
            f"`terraform state {rest[0]}` is dangerous; requires explicit override",
        )

    if sub == "apply":
        bad = sorted(set(rest) & _FORBIDDEN_APPLY_FLAGS)
        if bad:
            return Decision(
                False,
                f"apply must consume a saved plan; flags forbidden: {bad}",
            )
        if not _has_plan_file(rest):
            return Decision(
                False,
                "apply must be invoked with a saved plan file (positional arg)",
            )

    return Decision(True, "ok")


def require_allowed(args: Sequence[str], *, override: bool = False) -> None:
    """Raise :class:`TerraformOperationDenied` if the policy denies ``args``."""
    decision = evaluate(args, override=override)
    if not decision.allowed:
        raise TerraformOperationDenied(decision.reason)


def _has_plan_file(rest: list[str]) -> bool:
    """Return True if the apply argv carries a positional plan file path.

    A plan file is any non-flag argument that does not start with ``-``.
    """
    return any(not a.startswith("-") for a in rest)
