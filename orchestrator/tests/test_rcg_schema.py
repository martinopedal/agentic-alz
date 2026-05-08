"""Smoke test for the typed RCG schema and the in-repo lib example."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_alz.schema import SchemaValidationError, validate

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LIB_DIR = REPO_ROOT / "firewall-policy" / "lib"
LIB_RCG_FIXTURES = sorted(LIB_DIR.glob("*/rcg.json"))


def test_rcg_schema_loads() -> None:
    """The schema itself parses as a JSON Schema document."""
    from agentic_alz.schema import load

    schema = load("rcg")
    assert schema["title"].startswith("Typed Azure Firewall Rule Collection Group")


def test_lib_has_at_least_one_rcg_fixture() -> None:
    """Guard against the parametrised test silently passing on an empty set."""
    assert LIB_RCG_FIXTURES, (
        f"no rcg.json fixtures found under {LIB_DIR}; the lib must ship at "
        "least one pre-approved RCG"
    )


@pytest.mark.parametrize(
    "rcg_path",
    LIB_RCG_FIXTURES,
    ids=[p.parent.name for p in LIB_RCG_FIXTURES],
)
def test_lib_rcg_validates_against_schema(rcg_path: Path) -> None:
    """Every firewall-policy/lib/<pattern>/rcg.json must validate."""
    payload = json.loads(rcg_path.read_text(encoding="utf-8"))
    validate("rcg", payload)


def test_rcg_rejects_wildcard_fqdn() -> None:
    payload = {
        "schema_version": "1",
        "name": "bad-rcg",
        "priority": 400,
        "rule_collections": [
            {
                "name": "bad",
                "kind": "application",
                "priority": 100,
                "action": "Allow",
                "rules": [
                    {
                        "name": "bad-rule",
                        "kind": "application",
                        "protocols": [{"type": "Https", "port": 443}],
                        "destination_fqdns": ["*"],
                    }
                ],
            }
        ],
    }
    with pytest.raises(SchemaValidationError):
        validate("rcg", payload)


def test_rcg_rejects_wildcard_destination() -> None:
    payload = {
        "schema_version": "1",
        "name": "bad-rcg",
        "priority": 400,
        "rule_collections": [
            {
                "name": "bad",
                "kind": "network",
                "priority": 100,
                "action": "Allow",
                "rules": [
                    {
                        "name": "bad-rule",
                        "kind": "network",
                        "protocols": ["TCP"],
                        "destination_addresses": ["*"],
                        "destination_ports": ["443"],
                    }
                ],
            }
        ],
    }
    with pytest.raises(SchemaValidationError):
        validate("rcg", payload)


def test_rcg_rejects_priority_out_of_range() -> None:
    payload = {
        "schema_version": "1",
        "name": "bad",
        "priority": 50,  # below 100
        "rule_collections": [
            {
                "name": "x",
                "kind": "network",
                "priority": 100,
                "action": "Allow",
                "rules": [
                    {
                        "name": "r",
                        "kind": "network",
                        "protocols": ["TCP"],
                        "destination_ports": ["443"],
                    }
                ],
            }
        ],
    }
    with pytest.raises(SchemaValidationError):
        validate("rcg", payload)
