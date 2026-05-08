"""Tests for ``agentic-alz lab init``."""

from __future__ import annotations

import json
import tarfile
from pathlib import Path

import yaml
from click.testing import CliRunner

from agentic_alz.cli import main

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LAB_INPUTS = REPO_ROOT / "evals" / "golden" / "lab-hns" / "inputs.yaml"
PROD_INPUTS = REPO_ROOT / "evals" / "golden" / "hns-minimal" / "inputs.yaml"


def test_lab_init_emits_bundle(tmp_path: Path) -> None:
    runner = CliRunner()
    out = tmp_path / "lab-bundle.tar.gz"
    result = runner.invoke(main, ["lab", "init", "--inputs", str(LAB_INPUTS), "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert out.is_file()
    with tarfile.open(out, "r:gz") as tar:
        names = set(tar.getnames())
    # Core terraform files present.
    assert "main.tf" in names
    assert "terraform.tfvars.json" in names
    assert "lab-manifest.json" in names
    # Lab mode strips the production backend.tf so the operator gets local
    # state by default; the loud red banner in lab-mode.md tells them so.
    assert "backend.tf" not in names


def test_lab_init_refuses_non_sandbox(tmp_path: Path) -> None:
    runner = CliRunner()
    out = tmp_path / "lab-bundle.tar.gz"
    result = runner.invoke(main, ["lab", "init", "--inputs", str(PROD_INPUTS), "--out", str(out)])
    assert result.exit_code == 7
    assert "sandbox" in result.output
    assert not out.exists()


def test_lab_init_kill_switch(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AGENTIC_ALZ_DISABLED", "true")
    runner = CliRunner()
    out = tmp_path / "lab-bundle.tar.gz"
    result = runner.invoke(main, ["lab", "init", "--inputs", str(LAB_INPUTS), "--out", str(out)])
    assert result.exit_code == 2
    assert "kill switch" in result.output.lower()


def test_lab_init_refuses_invalid_inputs(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("schema_version: '1'\norg: {}\n", encoding="utf-8")
    runner = CliRunner()
    out = tmp_path / "lab-bundle.tar.gz"
    result = runner.invoke(main, ["lab", "init", "--inputs", str(bad), "--out", str(out)])
    assert result.exit_code == 1


def test_lab_inputs_are_schema_valid() -> None:
    """The lab golden inputs file is exercised by the CLI; sanity check it parses."""
    data = yaml.safe_load(LAB_INPUTS.read_text(encoding="utf-8"))
    assert data["tags"]["defaults"]["Environment"] == "sandbox"
    assert data["connectivity"]["firewall"]["sku"] == "Standard"


def test_lab_init_manifest_has_inputs_sha(tmp_path: Path) -> None:
    runner = CliRunner()
    out = tmp_path / "lab-bundle.tar.gz"
    result = runner.invoke(main, ["lab", "init", "--inputs", str(LAB_INPUTS), "--out", str(out)])
    assert result.exit_code == 0, result.output
    # Manifest is the trailing pretty-printed JSON object in stdout. Find it
    # by locating the last '{' that begins a complete JSON document.
    text = result.output
    start = text.rfind("\n{")
    assert start != -1, text
    payload = json.loads(text[start + 1 :])
    assert "inputs_sha256" in payload
    assert payload["bundle"].endswith("lab-bundle.tar.gz")
