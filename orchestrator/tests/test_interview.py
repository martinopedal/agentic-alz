"""Tests for the Interview stage runtime (offline + live gating)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from agentic_alz.cli import main
from agentic_alz.llm.guard import LLMOutputInvalid
from agentic_alz.llm.models import ModelNotAllowed, ModelRoleMismatch
from agentic_alz.stages.interview import (
    LiveModeNotImplemented,
    TranscriptError,
    TranscriptTurn,
    load_transcript,
    run_interview_live,
    run_interview_offline,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GOLDEN_TRANSCRIPT = REPO_ROOT / "evals" / "golden" / "interview-hns-minimal" / "transcript.jsonl"


def _terminal_assistant_json() -> str:
    lines = [
        line
        for line in GOLDEN_TRANSCRIPT.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return json.loads(lines[-1])["content"]


def test_load_transcript_ok() -> None:
    turns = load_transcript(GOLDEN_TRANSCRIPT)
    assert turns[-1].role == "assistant"
    assert turns[0].role in {"system", "user", "assistant"}


def test_load_transcript_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_transcript(tmp_path / "nope.jsonl")


def test_load_transcript_rejects_bad_role(tmp_path: Path) -> None:
    p = tmp_path / "t.jsonl"
    p.write_text(json.dumps({"role": "boss", "content": "hi"}) + "\n", encoding="utf-8")
    with pytest.raises(TranscriptError):
        load_transcript(p)


def test_load_transcript_rejects_non_string_content(tmp_path: Path) -> None:
    p = tmp_path / "t.jsonl"
    p.write_text(json.dumps({"role": "user", "content": 42}) + "\n", encoding="utf-8")
    with pytest.raises(TranscriptError):
        load_transcript(p)


def test_load_transcript_rejects_invalid_json(tmp_path: Path) -> None:
    p = tmp_path / "t.jsonl"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(TranscriptError):
        load_transcript(p)


def test_offline_happy_path() -> None:
    """Golden transcript whose terminal turn is a valid inputs JSON."""
    turns = load_transcript(GOLDEN_TRANSCRIPT)
    out = run_interview_offline(turns)
    assert out["schema_version"] == "1"
    assert out["org"]["short_code"] == "acme"
    # User free text containing 'ignore previous instructions' must NOT
    # leak into any string field of the output.
    serialised = json.dumps(out)
    assert "ignore previous instructions" not in serialised.lower()
    assert "tell me a joke" not in serialised.lower()


def test_offline_terminal_must_be_assistant() -> None:
    turns = [
        TranscriptTurn(role="user", content="hi"),
    ]
    with pytest.raises(TranscriptError):
        run_interview_offline(turns)


def test_offline_assistant_must_be_json_object() -> None:
    turns = [TranscriptTurn(role="assistant", content="not-json")]
    with pytest.raises(LLMOutputInvalid):
        run_interview_offline(turns)


def test_offline_rejects_schema_invalid() -> None:
    bad = json.dumps({"schema_version": "1", "org": {"short_code": "X"}})  # missing keys
    turns = [TranscriptTurn(role="assistant", content=bad)]
    with pytest.raises(LLMOutputInvalid):
        run_interview_offline(turns)


def test_offline_strips_forged_server_keys() -> None:
    """LLM cannot forge inputs_sha or override schema_version."""
    obj = json.loads(_terminal_assistant_json())
    obj["inputs_sha"] = "deadbeef"
    obj["schema_version"] = "999"  # adversarial
    turns = [TranscriptTurn(role="assistant", content=json.dumps(obj))]
    out = run_interview_offline(turns)
    assert out["schema_version"] == "1"
    assert "inputs_sha" not in out


def test_offline_empty_transcript_raises() -> None:
    with pytest.raises(TranscriptError):
        run_interview_offline([])


def test_live_rejects_non_allowlisted_model() -> None:
    turns = [TranscriptTurn(role="assistant", content="{}")]
    with pytest.raises(ModelNotAllowed):
        run_interview_live(turns, model_id="acme/synthwave-9000")


def test_live_rejects_wrong_role() -> None:
    """gpt-5.3-codex is allowlisted but not for the 'interview' role."""
    turns = [TranscriptTurn(role="assistant", content="{}")]
    with pytest.raises(ModelRoleMismatch):
        run_interview_live(turns, model_id="openai/gpt-5.3-codex")


def test_live_raises_not_implemented_for_allowlisted() -> None:
    turns = [TranscriptTurn(role="assistant", content="{}")]
    with pytest.raises(LiveModeNotImplemented):
        run_interview_live(turns, model_id="openai/gpt-5.4")


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------


def test_cli_interview_offline_writes_inputs(tmp_path: Path) -> None:
    runner = CliRunner()
    out = tmp_path / "inputs.yaml"
    result = runner.invoke(
        main,
        ["interview", "--transcript", str(GOLDEN_TRANSCRIPT), "--out", str(out)],
    )
    assert result.exit_code == 0, result.output
    assert out.is_file()
    assert "schema_version" in out.read_text(encoding="utf-8")


def test_cli_interview_live_without_model_errors() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["interview", "--transcript", str(GOLDEN_TRANSCRIPT), "--live"])
    assert result.exit_code == 1
    assert "--live requires --model" in result.output


def test_cli_interview_live_rejects_unallowlisted_model() -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "interview",
            "--transcript",
            str(GOLDEN_TRANSCRIPT),
            "--live",
            "--model",
            "acme/synthwave-9000",
        ],
    )
    assert result.exit_code == 4
    assert "frontier allowlist" in result.output


def test_cli_interview_live_allowlisted_model_not_implemented() -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "interview",
            "--transcript",
            str(GOLDEN_TRANSCRIPT),
            "--live",
            "--model",
            "openai/gpt-5.4",
        ],
    )
    assert result.exit_code == 6
    assert "not wired" in result.output
