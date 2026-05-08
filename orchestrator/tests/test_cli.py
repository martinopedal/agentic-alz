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


def test_judge_cli_reports_pass(tmp_path: Path) -> None:
    """`agentic-alz judge` returns 0 on unanimous PASS and prints markdown."""
    payload = {
        "rubric": ["cost", "policy"],
        "verdicts": [
            {
                "model_id": "anthropic/claude-opus-4.7",
                "criteria": [
                    {"criterion": "cost", "verdict": "pass", "rationale": "ok"},
                    {"criterion": "policy", "verdict": "pass", "rationale": "ok"},
                ],
            },
            {
                "model_id": "openai/gpt-5.4",
                "criteria": [
                    {"criterion": "cost", "verdict": "pass", "rationale": "ok"},
                    {"criterion": "policy", "verdict": "pass", "rationale": "ok"},
                ],
            },
        ],
    }
    p = tmp_path / "verdicts.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(main, ["judge", str(p)])
    assert result.exit_code == 0, result.output
    assert "PASS" in result.stdout


def test_judge_cli_fails_on_dissent(tmp_path: Path) -> None:
    payload = {
        "rubric": ["cost"],
        "verdicts": [
            {
                "model_id": "anthropic/claude-opus-4.7",
                "criteria": [{"criterion": "cost", "verdict": "fail", "rationale": "spendy"}],
            },
            {
                "model_id": "openai/gpt-5.4",
                "criteria": [{"criterion": "cost", "verdict": "pass", "rationale": "ok"}],
            },
        ],
    }
    p = tmp_path / "verdicts.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(main, ["judge", str(p)])
    assert result.exit_code == 5
    assert "FAIL" in result.stdout


def test_judge_cli_rejects_non_allowlisted_model(tmp_path: Path) -> None:
    payload = {
        "rubric": ["cost"],
        "verdicts": [
            {
                "model_id": "acme/synthwave-9000",
                "criteria": [{"criterion": "cost", "verdict": "pass", "rationale": "ok"}],
            },
            {
                "model_id": "openai/gpt-5.4",
                "criteria": [{"criterion": "cost", "verdict": "pass", "rationale": "ok"}],
            },
        ],
    }
    p = tmp_path / "verdicts.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(main, ["judge", str(p)])
    assert result.exit_code == 4
    assert "frontier allowlist" in result.stderr


def test_models_cli_lists_judges() -> None:
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(main, ["models", "--role", "judge"])
    assert result.exit_code == 0, result.output
    # Cross-provider diversity required for judges.
    providers = {line.split("\t")[1] for line in result.stdout.strip().splitlines()}
    assert len(providers) >= 2
