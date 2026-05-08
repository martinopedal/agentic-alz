"""End-to-end-ish CLI tests using Click's testing facilities."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from agentic_alz.cli import main


def test_validate_inputs_ok(golden_inputs_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["validate-inputs", str(golden_inputs_path)])
    assert result.exit_code == 0, result.output
    assert "OK" in result.output


def test_generate_writes_files(tmp_path: Path, golden_inputs_path: Path) -> None:
    runner = CliRunner()
    out = tmp_path / "alz-out"
    result = runner.invoke(
        main,
        ["generate", "--inputs", str(golden_inputs_path), "--out", str(out)],
    )
    assert result.exit_code == 0, result.output
    assert (out / "main.tf").is_file()
    assert (out / "terraform.tfvars.json").is_file()


def test_risk_command_emits_valid_report(tmp_path: Path) -> None:
    runner = CliRunner(mix_stderr=False)
    sample = Path(__file__).parent / "data" / "plan.sample.json"
    result = runner.invoke(
        main,
        ["--log-level", "ERROR", "risk", "--plan-json", str(sample), "--env", "platform"],
    )
    assert result.exit_code == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["schema_version"] == "1"
    assert report["weight"]["env"] == "platform"


def test_kill_switch_blocks_cli(monkeypatch, golden_inputs_path: Path) -> None:
    monkeypatch.setenv("AGENTIC_ALZ_DISABLED", "true")
    runner = CliRunner()
    result = runner.invoke(main, ["validate-inputs", str(golden_inputs_path)])
    assert result.exit_code == 2
    assert "kill switch" in result.output.lower()


def test_tf_policy_denies_destroy() -> None:
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(main, ["tf-policy", "destroy"])
    assert result.exit_code == 3
    payload = json.loads(result.stdout.strip().splitlines()[0])
    assert payload["allowed"] is False
