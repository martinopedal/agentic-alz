"""Global kill switch.

Reading the kill switch is a side-effect-free, stateless check of the
``AGENTIC_ALZ_DISABLED`` environment variable. Any value other than the
literal string ``"false"`` (case-insensitive) **or** an unset variable is
treated as enabled. The default is **enabled**, i.e. the orchestrator runs
unless explicitly disabled.

The disabled state is checked at the entry of every CLI command and at the
top of every stage transition. Stages that detect the disabled state exit
with a structured ``{"halted": true}`` event and a non-zero exit code so CI
fails loudly.
"""

from __future__ import annotations

import os

_ENV_VAR = "AGENTIC_ALZ_DISABLED"


def is_disabled() -> bool:
    """Return ``True`` if the kill switch is engaged.

    The kill switch is considered engaged when ``AGENTIC_ALZ_DISABLED`` is
    set to any truthy value (``"true"``, ``"1"``, ``"yes"``, ``"on"``).
    """
    raw = os.environ.get(_ENV_VAR, "").strip().lower()
    return raw in {"true", "1", "yes", "on"}


class KillSwitchEngaged(RuntimeError):
    """Raised when an entry point is invoked while the kill switch is on."""

    def __init__(self) -> None:
        super().__init__(
            "Agentic ALZ is disabled by the kill switch "
            f"({_ENV_VAR}). All scheduled and triggered runs are halted."
        )


def assert_enabled() -> None:
    """Raise :class:`KillSwitchEngaged` if the kill switch is on."""
    if is_disabled():
        raise KillSwitchEngaged
