"""Tests for the deterministic risk classifier."""

from __future__ import annotations

import copy

from agentic_alz.schema import validate
from agentic_alz.stages.risk import classify, count_actions, detect_flags


def test_count_actions_distinguishes_replace(sample_plan_json: dict) -> None:
    counts = count_actions(sample_plan_json)
    # plan has: 1 create (firewall), 1 update (law), 1 delete (storage),
    # 1 create (rbac), 1 replace (public ip).
    assert counts.add == 2
    assert counts.change == 1
    assert counts.destroy == 1
    assert counts.replace == 1


def test_detect_flags_covers_expected(sample_plan_json: dict) -> None:
    flags = set(detect_flags(sample_plan_json))
    assert "firewall" in flags
    assert "rbac" in flags
    assert "destructive" in flags
    assert "data-deletion-risk" in flags  # because storage account deletion
    assert "public-exposure" in flags  # because public IP create


def test_classify_validates_against_schema(sample_plan_json: dict) -> None:
    report = classify(sample_plan_json, env="platform", infracost_delta_usd=123.45)
    validate("risk", report)


def test_classify_blocks_auto_apply_for_platform(sample_plan_json: dict) -> None:
    report = classify(sample_plan_json, env="platform")
    assert report["blocks_auto_apply"] is True


def test_classify_does_not_block_auto_apply_for_workload(sample_plan_json: dict) -> None:
    report = classify(sample_plan_json, env="workload")
    assert report["blocks_auto_apply"] is False


def test_classify_requires_second_reviewer_when_rbac(sample_plan_json: dict) -> None:
    report = classify(sample_plan_json, env="workload")
    assert report["requires_second_reviewer"] is True


def test_classify_clean_plan_has_zero_score() -> None:
    empty_plan = {"resource_changes": []}
    report = classify(empty_plan, env="platform")
    assert report["score"] == 0.0
    assert report["flags"] == []
    assert report["requires_second_reviewer"] is False


def test_classify_unknown_env_raises(sample_plan_json: dict) -> None:
    import pytest

    with pytest.raises(ValueError, match="unknown env"):
        classify(sample_plan_json, env="prod")  # not in ENV_WEIGHTS


def test_infracost_delta_negative_does_not_subtract(sample_plan_json: dict) -> None:
    a = classify(sample_plan_json, env="platform", infracost_delta_usd=0.0)
    b = classify(sample_plan_json, env="platform", infracost_delta_usd=-1000.0)
    # Negative deltas (cost decreases) are clamped to zero contribution.
    assert a["score"] == b["score"]


def test_replace_counts_toward_destroy_in_score(sample_plan_json: dict) -> None:
    # If we remove the replace from the sample, score should drop by env_weight.
    plan = copy.deepcopy(sample_plan_json)
    plan["resource_changes"] = [
        rc for rc in plan["resource_changes"] if rc["type"] != "azurerm_public_ip"
    ]
    a = classify(sample_plan_json, env="platform")
    b = classify(plan, env="platform")
    # also drops the public-exposure flag (-25), so net change is 10 + 25 = 35.
    assert a["score"] - b["score"] == 35.0
