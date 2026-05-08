"""Structured logging configured once per process.

All orchestrator entry points configure :mod:`structlog` to emit JSON lines
with a stable schema:

* ``ts`` — ISO-8601 timestamp.
* ``level`` — ``info``/``warn``/``error``.
* ``trace_id`` — generated per orchestrator run; threaded via ``contextvars``.
* ``stage`` — the current pipeline stage, when in one.
* ``event`` — event name (e.g. ``stage.start``, ``tool.call``, ``checkpoint.write``).
* additional, structured key/value pairs.

These logs are designed to be shipped to Log Analytics with no transform.
"""

from __future__ import annotations

import logging
import sys
import uuid
from contextvars import ContextVar

import structlog

_trace_id: ContextVar[str] = ContextVar("trace_id", default="")
_stage: ContextVar[str] = ContextVar("stage", default="")


def configure(level: str = "INFO") -> None:
    """Idempotently configure structlog and stdlib logging for JSON output."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=level,
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _add_trace_and_stage,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level)),
        cache_logger_on_first_use=True,
    )


def new_trace_id() -> str:
    """Generate and bind a fresh trace ID for the current context."""
    tid = uuid.uuid4().hex
    _trace_id.set(tid)
    return tid


def set_stage(name: str) -> None:
    """Bind the current pipeline stage name to the logging context."""
    _stage.set(name)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger configured for this process."""
    return structlog.get_logger(name)


def _add_trace_and_stage(_logger: object, _name: str, event_dict: dict) -> dict:
    tid = _trace_id.get()
    if tid:
        event_dict.setdefault("trace_id", tid)
    stg = _stage.get()
    if stg:
        event_dict.setdefault("stage", stg)
    return event_dict
