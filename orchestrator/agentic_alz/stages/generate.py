"""Generate stage — deterministic, template-based.

The Generate stage takes a validated ``inputs.yaml`` and a ``design.json``,
and writes a ready-to-validate Terraform working directory under the chosen
output path. It is intentionally not LLM-driven: the LLM's job ended at
Design.

For v1 we copy the entire ``templates/<topology>/`` directory verbatim and
emit a ``terraform.tfvars.json`` derived from the inputs. The OPA policy
``avm_pinning.rego`` then asserts that every module in the rendered template
is present in ``versions.lock`` with the same exact version string.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from ..hashing import sha256_json

# Topologies supported in v1 (vWAN deferred).
SUPPORTED_TOPOLOGIES = frozenset({"hub-and-spoke"})


class UnsupportedTopology(ValueError):
    """Raised when ``inputs.connectivity.topology`` is not yet supported."""


def _templates_root() -> Path:
    """Resolve the ``templates/`` directory at the repo root."""
    here = Path(__file__).resolve()
    # orchestrator/agentic_alz/stages/generate.py -> repo root
    return here.parent.parent.parent.parent / "templates"


def generate(inputs: dict[str, Any], out_dir: str | Path) -> dict[str, Any]:
    """Render the Terraform working directory for ``inputs``.

    Args:
        inputs: Validated ``inputs.yaml`` content (caller is responsible for
            having run :func:`agentic_alz.schema.validate`).
        out_dir: Destination directory; created if missing. Existing files in
            the destination are overwritten; files unique to the destination
            are left in place (callers needing a clean directory must remove
            it first).

    Returns:
        A small manifest describing what was rendered.

    Raises:
        UnsupportedTopology: the requested topology is not supported in v1.
        FileNotFoundError: the source template directory is missing.
    """
    topology = inputs["connectivity"]["topology"]
    if topology not in SUPPORTED_TOPOLOGIES:
        raise UnsupportedTopology(
            f"topology {topology!r} not supported in v1 (supported: "
            f"{sorted(SUPPORTED_TOPOLOGIES)})"
        )

    src = _templates_root() / topology
    if not src.is_dir():
        raise FileNotFoundError(f"template directory missing: {src}")

    dst = Path(out_dir)
    dst.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    for path in sorted(src.rglob("*")):
        if path.is_dir():
            continue
        rel = path.relative_to(src)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied.append(str(rel))

    tfvars = _to_tfvars(inputs)
    (dst / "terraform.tfvars.json").write_text(
        json.dumps(tfvars, indent=2, sort_keys=True), encoding="utf-8"
    )
    copied.append("terraform.tfvars.json")

    return {
        "topology": topology,
        "out_dir": str(dst),
        "files": copied,
        "inputs_sha256": sha256_json(inputs),
    }


def _to_tfvars(inputs: dict[str, Any]) -> dict[str, Any]:
    """Project ``inputs.yaml`` keys onto the template's variable surface.

    The template's ``variables.tf`` declares one variable per top-level key in
    the input schema, so this projection is intentionally direct: it takes
    only the fields the template actually consumes and drops the rest.
    """
    keys = (
        "org",
        "tenant",
        "management_groups",
        "platform_subscriptions",
        "regions",
        "connectivity",
        "logging",
        "policy_baseline",
        "naming",
        "tags",
    )
    return {k: inputs[k] for k in keys if k in inputs}
