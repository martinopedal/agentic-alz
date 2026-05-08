"""Schema loading and JSON Schema validation.

Schemas live in ``schemas/`` at the repo root. This module:

* Locates them deterministically using the package install path (works when
  the orchestrator is installed in editable mode and when shipped as a wheel
  alongside a copy of the schemas/ directory).
* Caches parsed schemas.
* Provides :func:`validate` which raises :class:`SchemaValidationError` with
  a structured error list rather than jsonschema's default exception, so the
  CLI can render a useful message.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


@dataclass(frozen=True)
class SchemaError:
    """Single schema validation failure."""

    path: str
    message: str


class SchemaValidationError(ValueError):
    """Raised when an instance fails JSON Schema validation."""

    def __init__(self, schema_id: str, errors: list[SchemaError]) -> None:
        self.schema_id = schema_id
        self.errors = errors
        joined = "\n".join(f"  {e.path}: {e.message}" for e in errors)
        super().__init__(f"{schema_id} validation failed:\n{joined}")


def _schemas_dir() -> Path:
    """Return the path to the schemas directory.

    The orchestrator is installed from ``orchestrator/`` and the schemas live
    next to it at the repo root. We resolve them relative to this file rather
    than relying on cwd.
    """
    here = Path(__file__).resolve()
    # orchestrator/agentic_alz/schema.py -> repo root
    return here.parent.parent.parent / "schemas"


@cache
def load(name: str) -> dict[str, Any]:
    """Load a named schema (e.g. ``"inputs"``).

    Args:
        name: schema base name without the ``.schema.json`` suffix.
    """
    path = _schemas_dir() / f"{name}.schema.json"
    if not path.is_file():
        raise FileNotFoundError(f"schema not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def validate(name: str, instance: Any) -> None:
    """Validate ``instance`` against the named schema.

    Raises:
        SchemaValidationError: aggregated list of all violations.
    """
    schema = load(name)
    validator = Draft202012Validator(schema)
    raw_errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
    if not raw_errors:
        return
    errors = [
        SchemaError(
            path="/".join(str(p) for p in e.absolute_path) or "<root>",
            message=e.message,
        )
        for e in raw_errors
    ]
    raise SchemaValidationError(schema_id=schema.get("$id", name), errors=errors)
