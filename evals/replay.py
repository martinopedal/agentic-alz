#!/usr/bin/env python3
"""Offline replay harness for golden runs.

A golden run is a directory under ``evals/golden/<case>/`` containing at least
``inputs.yaml``. The replay harness exercises every deterministic stage of
the pipeline against those inputs:

1. Validate ``inputs.yaml`` against the schema.
2. Generate a Terraform working directory (idempotent — written to a temp
   directory).
3. Run conftest's AVM-pinning policy against the generated files (best-effort
   if conftest is not on PATH; skipped with a warning otherwise).
4. If a fixture ``plan.json`` exists, run the risk classifier and validate
   the resulting risk report against its schema.

The harness does **not** invoke Terraform or any LLM. Production eval runs
that deploy to the sandbox subscription live in ``.github/workflows/eval.yml``
behind the ``eval-sandbox`` environment.

Exit code 0 = all golden cases passed, non-zero otherwise.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "orchestrator"))

from agentic_alz.schema import SchemaValidationError, validate  # noqa: E402
from agentic_alz.stages.generate import generate  # noqa: E402
from agentic_alz.stages.risk import classify  # noqa: E402


def run(case_dir: Path) -> list[str]:
    """Run the harness against a single golden case; return list of failures."""
    failures: list[str] = []

    inputs_path = case_dir / "inputs.yaml"
    if not inputs_path.is_file():
        return [f"{case_dir}: missing inputs.yaml"]

    inputs = yaml.safe_load(inputs_path.read_text(encoding="utf-8"))
    try:
        validate("inputs", inputs)
    except SchemaValidationError as exc:
        failures.append(f"{case_dir}: inputs schema invalid: {exc}")
        return failures

    with tempfile.TemporaryDirectory(prefix="alz-eval-") as out:
        out_path = Path(out)
        try:
            manifest = generate(inputs, out_path)
        except Exception as exc:  # noqa: BLE001 - any failure is a failure
            failures.append(f"{case_dir}: generate failed: {exc}")
            return failures
        if "main.tf" not in manifest["files"]:
            failures.append(f"{case_dir}: generate produced no main.tf")

        if shutil.which("conftest"):
            tf_files = list(out_path.glob("*.tf"))
            try:
                subprocess.run(
                    [
                        "conftest",
                        "test",
                        "--parser",
                        "hcl2",
                        "--policy",
                        str(REPO_ROOT / "policies"),
                        "--namespace",
                        "alz.avm_pinning",
                        *map(str, tf_files),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as exc:
                failures.append(
                    f"{case_dir}: conftest avm_pinning denied: {exc.stdout}{exc.stderr}"
                )
        else:
            print(f"::warning::conftest not on PATH; skipping policy check for {case_dir}")

    plan_fixture = case_dir / "plan.json"
    if plan_fixture.is_file():
        plan = json.loads(plan_fixture.read_text(encoding="utf-8"))
        report = classify(plan, env="sandbox", infracost_delta_usd=0.0)
        try:
            validate("risk", report)
        except SchemaValidationError as exc:
            failures.append(f"{case_dir}: risk report invalid: {exc}")

    return failures


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        # Default to all golden cases.
        cases = sorted(p for p in (REPO_ROOT / "evals" / "golden").iterdir() if p.is_dir())
    else:
        cases = [Path(p) for p in argv[1:]]
    if not cases:
        print("no golden cases found", file=sys.stderr)
        return 1

    all_failures: list[str] = []
    for c in cases:
        print(f"== replaying {c.name} ==")
        all_failures.extend(run(c))

    if all_failures:
        print("\n=== FAILURES ===", file=sys.stderr)
        for f in all_failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("\nAll golden cases passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
