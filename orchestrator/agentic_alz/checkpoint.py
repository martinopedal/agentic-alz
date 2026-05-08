"""Replayable run checkpoints.

Every stage produces a checkpoint blob that captures:

* Stage name and version.
* Input SHA, output SHA.
* Tool calls made (name, args sha, duration, exit status).
* Identity used (workload identity client ID; never a secret).
* Commit SHA of the orchestrator code that ran.

Checkpoints are written to a content-addressed local directory in dev runs
and to a versioned blob container in production. The shape is identical;
only the storage backend differs.

Replay = re-run the stage with the exact input recorded in its checkpoint.
This makes incident postmortems and CI failure debugging deterministic.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .hashing import canonical_json, sha256_bytes


@dataclass
class ToolCall:
    """A single external tool invocation recorded in a checkpoint."""

    name: str
    args_sha256: str
    started_at: float
    duration_s: float
    exit_status: int
    truncated_stderr_tail: str = ""


@dataclass
class Checkpoint:
    """One stage's full execution record."""

    trace_id: str
    stage: str
    stage_version: str
    started_at: float
    ended_at: float
    input_sha256: str
    output_sha256: str
    identity_client_id: str
    orchestrator_commit_sha: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    halted: bool = False
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CheckpointStore:
    """Local-filesystem checkpoint store.

    Layout::

        <root>/<trace_id>/<stage>-<index>.json

    The store is append-only by convention; nothing in this module overwrites
    an existing file.
    """

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def write(self, cp: Checkpoint) -> Path:
        """Write ``cp`` to disk and return the path written.

        The file name embeds a monotonically increasing index per
        ``(trace_id, stage)`` pair so multiple invocations of the same stage
        can coexist (e.g. a re-run of Validate after a fixup).
        """
        run_dir = self._root / cp.trace_id
        run_dir.mkdir(parents=True, exist_ok=True)
        index = self._next_index(run_dir, cp.stage)
        path = run_dir / f"{cp.stage}-{index:04d}.json"
        payload = canonical_json(cp.to_dict())
        # Self-check: write the SHA of the payload alongside, so a future
        # reader can detect tampering.
        sha_path = path.with_suffix(".sha256")
        path.write_bytes(payload)
        sha_path.write_text(sha256_bytes(payload), encoding="utf-8")
        return path

    @staticmethod
    def _next_index(run_dir: Path, stage: str) -> int:
        existing = list(run_dir.glob(f"{stage}-*.json"))
        return len(existing) + 1


def commit_sha() -> str:
    """Best-effort orchestrator commit SHA; unknown -> ``"unknown"``."""
    return os.environ.get("GITHUB_SHA") or os.environ.get("GIT_COMMIT") or "unknown"


def now() -> float:
    """Wall-clock seconds; isolated for test override."""
    return time.time()


def write_simple(
    *,
    store: CheckpointStore,
    trace_id: str,
    stage: str,
    stage_version: str,
    input_obj: Any,
    output_obj: Any,
    identity_client_id: str = "local-dev",
    started_at: float | None = None,
    halted: bool = False,
    error: str | None = None,
    tool_calls: list[ToolCall] | None = None,
) -> Path:
    """Convenience helper: build a Checkpoint from typed args and persist it."""
    started_at = started_at if started_at is not None else now()
    cp = Checkpoint(
        trace_id=trace_id,
        stage=stage,
        stage_version=stage_version,
        started_at=started_at,
        ended_at=now(),
        input_sha256=_sha(input_obj),
        output_sha256=_sha(output_obj),
        identity_client_id=identity_client_id,
        orchestrator_commit_sha=commit_sha(),
        tool_calls=list(tool_calls or []),
        halted=halted,
        error=error,
    )
    return store.write(cp)


def _sha(obj: Any) -> str:
    """Stable SHA for any JSON-serialisable object (or empty string for None)."""
    if obj is None:
        return ""
    if isinstance(obj, (bytes, bytearray)):
        return sha256_bytes(bytes(obj))
    if isinstance(obj, str):
        return sha256_bytes(obj.encode("utf-8"))
    return sha256_bytes(canonical_json(obj))


# Re-export for convenience.
__all__ = [
    "Checkpoint",
    "CheckpointStore",
    "ToolCall",
    "commit_sha",
    "write_simple",
]


def load(path: str | Path) -> Checkpoint:
    """Load a checkpoint file written by :meth:`CheckpointStore.write`."""
    raw = Path(path).read_bytes()
    data = json.loads(raw.decode("utf-8"))
    tcs = [ToolCall(**tc) for tc in data.pop("tool_calls", [])]
    return Checkpoint(tool_calls=tcs, **data)
