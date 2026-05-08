"""Post-apply drift-detection cooldown.

After a successful ``terraform apply`` we suppress drift findings on the
affected state file for a fixed window. This breaks the well-known loop where
the apply itself appears as drift on the next nightly run.

The cooldown is a content-addressed file under the orchestrator's checkpoint
root; production deployments should mirror this to a versioned blob.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

DEFAULT_COOLDOWN_S = 2 * 60 * 60  # 2 hours, per the consensus plan


class CooldownStore:
    """File-backed cooldown registry keyed by state-file identifier."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def mark_applied(self, state_id: str, *, now: float | None = None) -> None:
        """Record that ``state_id`` was just applied."""
        ts = now if now is not None else time.time()
        path = self._path(state_id)
        path.write_text(json.dumps({"applied_at": ts}), encoding="utf-8")

    def is_in_cooldown(
        self,
        state_id: str,
        *,
        cooldown_s: int = DEFAULT_COOLDOWN_S,
        now: float | None = None,
    ) -> bool:
        """Return True if ``state_id`` is still within its post-apply cooldown."""
        path = self._path(state_id)
        if not path.is_file():
            return False
        try:
            applied_at = float(json.loads(path.read_text(encoding="utf-8"))["applied_at"])
        except (KeyError, ValueError, json.JSONDecodeError):
            return False
        ts = now if now is not None else time.time()
        return (ts - applied_at) < cooldown_s

    def _path(self, state_id: str) -> Path:
        # State IDs may contain slashes (e.g. "alz-platform/eu-west"); flatten.
        safe = state_id.replace("/", "__").replace("\\", "__")
        return self._root / f"{safe}.cooldown.json"
