"""Agentic ALZ orchestrator.

This package is the deterministic GitOps pipeline that drives the Azure
Landing Zone deploy and operate workflow. LLM-powered stages are isolated
behind strict JSON Schema contracts (see ``agentic_alz.llm.guard``).

The orchestrator's runtime guarantees:

* Apply is never invoked from this package; it lives in CI workflows.
* Every stage produces a checkpoint blob (replayable runbook).
* A global kill switch (``AGENTIC_ALZ_DISABLED`` env var) halts all entry
  points before any external side effect.
"""

from __future__ import annotations

__version__ = "0.1.0"
