"""Smoke test for the typed RCG schema and the in-repo lib example."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_alz.schema import SchemaValidationError, validate

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RCG_FIXTURE = REPO_ROOT / "firewall-policy" / "lib" / "allow-aks-to-mcr" / "rcg.json"


def test_rcg_schema_loads() -> None:
    """The schema itself parses as a JSON Schema document."""
    from agentic_alz.schema import load

    schema = load("rcg")
    assert schema["title"].startswith("Typed Azure Firewall Rule Collection Group")


def test_lib_example_validates_against_rcg_schema() -> None:
    payload = json.loads(RCG_FIXTURE.read_text(encoding="utf-8"))
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
