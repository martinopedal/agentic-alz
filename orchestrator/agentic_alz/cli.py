"""``agentic-alz`` CLI entry point.

The CLI is intentionally tiny: it exposes the deterministic stages so they
can be invoked from CI or locally without spinning up the full LangGraph
orchestrator. LLM stages are not exposed here in v1 — they require a
configured provider and are exercised through the orchestrator runtime.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
import yaml

from . import __version__
from . import logging as alog
from .killswitch import KillSwitchEngaged, assert_enabled
from .llm.judge import aggregate, from_json
from .llm.models import ModelNotAllowed, ModelRoleMismatch, models_for_role
from .schema import SchemaValidationError, validate
from .stages.generate import UnsupportedTopology, generate
from .stages.risk import classify
from .terraform.wrapper import TerraformOperationDenied, evaluate


@click.group()
@click.version_option(__version__, prog_name="agentic-alz")
@click.option(
    "--log-level",
    default="INFO",
    show_default=True,
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
)
def main(log_level: str) -> None:
    """Agentic ALZ — GitOps pipeline orchestrator for Azure Landing Zones."""
    alog.configure(level=log_level.upper())
    alog.new_trace_id()
    try:
        assert_enabled()
    except KillSwitchEngaged as exc:
        click.echo(str(exc), err=True)
        sys.exit(2)


@main.command("validate-inputs")
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def validate_inputs(path: Path) -> None:
    """Validate an inputs.yaml against schemas/inputs.schema.json."""
    log = alog.get_logger(__name__)
    alog.set_stage("validate-inputs")
    data = _load_yaml_or_json(path)
    try:
        validate("inputs", data)
    except SchemaValidationError as exc:
        log.error("inputs.invalid", path=str(path), errors=[e.__dict__ for e in exc.errors])
        click.echo(str(exc), err=True)
        sys.exit(1)
    log.info("inputs.valid", path=str(path))
    click.echo("OK")


@main.command("generate")
@click.option(
    "--inputs",
    "inputs_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--out",
    "out_dir",
    type=click.Path(file_okay=False, path_type=Path),
    required=True,
)
def generate_cmd(inputs_path: Path, out_dir: Path) -> None:
    """Render the Terraform working directory for the given inputs."""
    log = alog.get_logger(__name__)
    alog.set_stage("generate")
    data = _load_yaml_or_json(inputs_path)
    try:
        validate("inputs", data)
    except SchemaValidationError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)
    try:
        manifest = generate(data, out_dir)
    except UnsupportedTopology as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)
    log.info("generate.done", **manifest)
    click.echo(json.dumps(manifest, indent=2, sort_keys=True))


@main.command("risk")
@click.option(
    "--plan-json",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Terraform `terraform show -json plan.tfplan` output.",
)
@click.option(
    "--env",
    type=click.Choice(["sandbox", "platform", "workload"]),
    default="platform",
    show_default=True,
)
@click.option(
    "--infracost-delta-usd",
    type=float,
    default=0.0,
    show_default=True,
)
def risk_cmd(plan_json: Path, env: str, infracost_delta_usd: float) -> None:
    """Compute the risk report for a Terraform plan."""
    log = alog.get_logger(__name__)
    alog.set_stage("risk")
    plan = json.loads(plan_json.read_text(encoding="utf-8"))
    report = classify(plan, env=env, infracost_delta_usd=infracost_delta_usd)
    try:
        validate("risk", report)
    except SchemaValidationError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)
    log.info("risk.done", score=report["score"], flags=report["flags"])
    click.echo(json.dumps(report, indent=2, sort_keys=True))


@main.command("tf-policy")
@click.argument("argv", nargs=-1, required=True)
@click.option(
    "--override",
    is_flag=True,
    default=False,
    help="Permit destructive subcommands. CI-only.",
)
def tf_policy(argv: tuple[str, ...], override: bool) -> None:
    """Evaluate a Terraform CLI argv against the v1 safety policy."""
    decision = evaluate(list(argv), override=override)
    click.echo(json.dumps({"allowed": decision.allowed, "reason": decision.reason}))
    if not decision.allowed:
        try:
            raise TerraformOperationDenied(decision.reason)
        except TerraformOperationDenied:
            sys.exit(3)


@main.command("judge")
@click.argument(
    "verdicts_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--required-pass-votes",
    type=int,
    default=None,
    help="Pass threshold per criterion. Default = unanimous.",
)
@click.option(
    "--role",
    type=click.Choice(sorted({"design", "judge", "drift_triage", "firewall_compose"})),
    default="judge",
    show_default=True,
)
def judge_cmd(
    verdicts_path: Path,
    required_pass_votes: int | None,
    role: str,
) -> None:
    """Aggregate per-model verdicts into a build-time consensus report.

    The input file is JSON in the shape documented at
    `orchestrator.agentic_alz.llm.judge.from_json`. The orchestrator does
    NOT call models from this command — caller fans out to allowlisted
    models and records their structured verdicts.
    """
    log = alog.get_logger(__name__)
    alog.set_stage("judge")
    payload = json.loads(verdicts_path.read_text(encoding="utf-8"))
    verdicts, rubric = from_json(payload)
    try:
        report = aggregate(
            verdicts,
            rubric=rubric,
            required_pass_votes=required_pass_votes,
            role=role,
        )
    except (ModelNotAllowed, ModelRoleMismatch) as exc:
        click.echo(str(exc), err=True)
        sys.exit(4)
    log.info(
        "judge.done",
        overall_pass=report.overall_pass,
        models=list(report.models),
        threshold=report.required_pass_votes,
    )
    click.echo(report.summary_markdown)
    if not report.overall_pass:
        sys.exit(5)


@main.command("models")
@click.option(
    "--role",
    type=click.Choice(sorted({"interview", "design", "drift_triage", "firewall_compose", "judge"})),
    required=True,
)
def models_cmd(role: str) -> None:
    """List allowlisted frontier models for a stage role."""
    for entry in models_for_role(role):
        click.echo(f"{entry.id}\t{entry.provider}\t{entry.notes}")


def _load_yaml_or_json(path: Path) -> object:
    """Load YAML *or* JSON; YAML loader handles both."""
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text)


if __name__ == "__main__":  # pragma: no cover
    main()
