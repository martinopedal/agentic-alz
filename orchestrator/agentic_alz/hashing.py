"""Hashing utilities for canonical content addressing.

Several pieces of the orchestrator rely on stable content hashes:

* The Design stage records the SHA-256 of the ``inputs.yaml`` it consumed.
* The Risk stage records the SHA-256 of the saved ``terraform plan`` artifact.
* Checkpoints are keyed by the SHA-256 of their canonical-JSON payload.

To avoid the classic "two equivalent JSONs hash differently" trap we always
serialise via :func:`canonical_json` (sorted keys, no whitespace, UTF-8).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def canonical_json(value: Any) -> bytes:
    """Return the canonical JSON encoding of ``value`` as UTF-8 bytes.

    Canonical form: sorted keys, no insignificant whitespace, ``ensure_ascii``
    disabled (so non-ASCII characters are encoded as themselves rather than
    escape sequences). Floats are emitted in their shortest round-trippable
    form by Python's default JSON encoder; callers should avoid floats in
    content-hashed structures.
    """
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    """SHA-256 hex digest of ``data``."""
    return hashlib.sha256(data).hexdigest()


def sha256_json(value: Any) -> str:
    """SHA-256 hex digest of the canonical-JSON form of ``value``."""
    return sha256_bytes(canonical_json(value))


def sha256_file(path: str | Path) -> str:
    """SHA-256 hex digest of the file at ``path``, streaming."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
