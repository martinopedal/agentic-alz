"""Per-stage budgets: LLM token caps and tool-invocation timeouts.

These exist so a confused or compromised LLM cannot spend unbounded money or
hang the pipeline. Budgets are read from environment variables at process
start and held immutable for the run; stages compare their accumulated
consumption to the cap and raise :class:`BudgetExceeded` on overrun.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_TOKEN_BUDGET = 200_000
DEFAULT_TOOL_TIMEOUT_S = 1800  # 30 min
DEFAULT_APPLY_TIMEOUT_S = 1800  # 30 min on terraform apply


class BudgetExceeded(RuntimeError):
    """Raised when a stage's token cap or a tool's timeout is exceeded."""


@dataclass(frozen=True)
class Budget:
    """Immutable per-run budget envelope.

    Attributes:
        token_budget: Maximum input + output tokens an LLM stage may consume.
        tool_timeout_s: Wall-clock timeout for any single external tool call.
        apply_timeout_s: Wall-clock timeout specifically for ``terraform
            apply``. Surfaced separately because applies legitimately take
            longer than other tools.
    """

    token_budget: int = DEFAULT_TOKEN_BUDGET
    tool_timeout_s: int = DEFAULT_TOOL_TIMEOUT_S
    apply_timeout_s: int = DEFAULT_APPLY_TIMEOUT_S

    @classmethod
    def from_env(cls) -> Budget:
        """Build a :class:`Budget` from environment variables."""
        return cls(
            token_budget=_int_env("LLM_TOKEN_BUDGET", DEFAULT_TOKEN_BUDGET),
            tool_timeout_s=_int_env("TOOL_TIMEOUT_S", DEFAULT_TOOL_TIMEOUT_S),
            apply_timeout_s=_int_env("APPLY_TIMEOUT_S", DEFAULT_APPLY_TIMEOUT_S),
        )


class TokenMeter:
    """Tracks accumulated token consumption for a single stage invocation."""

    def __init__(self, budget: Budget) -> None:
        self._budget = budget
        self._used = 0

    @property
    def used(self) -> int:
        return self._used

    @property
    def remaining(self) -> int:
        return max(self._budget.token_budget - self._used, 0)

    def charge(self, tokens: int) -> None:
        """Add tokens to the meter; raise if the cap is exceeded.

        Args:
            tokens: Non-negative number of tokens to charge.

        Raises:
            ValueError: ``tokens`` is negative.
            BudgetExceeded: charging would exceed :attr:`Budget.token_budget`.
        """
        if tokens < 0:
            raise ValueError("tokens must be non-negative")
        new_total = self._used + tokens
        if new_total > self._budget.token_budget:
            raise BudgetExceeded(
                f"token budget exceeded: {new_total} > {self._budget.token_budget}"
            )
        self._used = new_total


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"environment variable {name}={raw!r} is not an integer") from exc
    if value <= 0:
        raise ValueError(f"environment variable {name}={value} must be > 0")
    return value
