# Incident response

## Severity matrix

| Sev | Definition | Examples | Response SLA |
| --- | --- | --- | --- |
| 1 | Active compromise or production impact | Unknown role assignment at platform Owner; Terraform state tampered; firewall opened to `0.0.0.0/0` | 15 min ack, 1 h status |
| 2 | Risk of imminent impact, controls bypassed | OIDC token leak suspected; CI applied a plan never reviewed; kill switch failed | 1 h ack, 4 h status |
| 3 | Degraded automation, no production impact | Drift detector loop; eval harness flaking; LLM provider outage | Next business day |

## First five minutes

1. **Set the kill switch.** `AGENTIC_ALZ_DISABLED=true` at the repo level.
2. **Page the on-call.** Use the channel in the operator's runbook (out of
   scope for this repo).
3. **Open an incident issue** in this repo with label `incident` and the
   severity. Do not put secrets in the issue.
4. **Snapshot evidence.** Pin the relevant workflow runs and Activity Log
   queries. Activity Log retention is 90 d — export anything older.

## Roles

- **Incident commander.** Coordinates; not hands-on.
- **Operator.** Holds `alz-apply-platform` JIT access; only one operator at a
  time.
- **Scribe.** Maintains the timeline in the incident issue.
- **Comms.** Internal stakeholder updates.

## Specific playbooks

### Compromised CI / OIDC token

See `runbook.md` "Compromised OIDC identity". After containment:

- Audit all PRs merged in the suspected window for unintended changes to
  `*.tf`, `versions.lock`, `policies/`, `.github/workflows/`.
- Force-rotate every federated credential, not only the suspected one.
- Require manual re-approval of all environments before lifting kill switch.

### Malicious or hallucinated firewall change

If a rule allowing wide egress / ingress is detected:

1. In the firewall portal, **disable** (not delete) the rule collection group
   to preserve evidence.
2. Open Sev-1 incident.
3. Identify the originating PR; revert via the normal pipeline.
4. Add a regression test in `policies/firewall_rules.rego` that would have
   denied the merge.

### Eval harness leaked into production

If a golden run accidentally targeted a non-sandbox subscription:

1. Confirm spend cap held; if it did not, escalate to billing immediately.
2. `terraform destroy` against the eval state (this is the only path where
   destroy is permitted, and only via the `eval` workflow).
3. File RCA: how did the wrong subscription ID enter the eval harness?

## Post-incident

- 5-day RCA in `docs/incidents/YYYY-MM-DD-shortname.md`.
- At least one new automated control (CI check, OPA rule, alert) per Sev-1.
- Review and update this document.
