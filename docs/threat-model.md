# Threat model

Scope: the Agentic ALZ orchestrator and its CI/CD path into Azure. Out of
scope: tenant-level Entra ID hardening (assumed to follow Microsoft's secure
score baseline), workload-internal threats.

## Assets

1. **State files** in the management subscription's storage account. Loss or
   tampering allows an attacker to silently mis-deploy.
2. **OIDC-federated Entra ID app registrations** (`alz-apply-platform`,
   `alz-apply-firewall`). Compromise yields Owner on the platform MG.
3. **Generated Terraform** in `alz-platform/` and downstream repos. Tampering
   produces a malicious plan that may pass review.
4. **Prompts and prompt inputs.** A prompt-injection in `inputs.yaml` could
   coerce the Design or Drift Triage agent into emitting harmful artifacts.
5. **Eval sandbox subscription.** Contains real Azure resources during golden
   runs; spend cap protects budget but not data.

## Attackers

- **Malicious contributor / supply-chain.** Pushes a PR that subtly changes a
  template or AVM module pin.
- **Compromised LLM provider response.** Returns adversarial JSON intended to
  defeat schema validation.
- **Compromised dependency.** A pulled Python or Terraform module ships a
  backdoor.
- **Stolen GitHub Actions OIDC token.** Replayed against Azure.
- **Insider with Reader on the tenant.** Reads state, harvests config.

## Mitigations (mapped to controls in this repo)

| Threat | Mitigation | Where |
| --- | --- | --- |
| Tampered state | Storage RBAC-only, CMK, soft-delete + versioning, private endpoint | `bootstrap/phase1.sh`, `docs/phase-0-prerequisites.md` |
| Malicious PR | CODEOWNERS + branch protection + required status checks; OPA conformance; signed commits | `CODEOWNERS`, `.github/workflows/validate.yml`, `policies/` |
| Prompt injection | JSON-Schema validation **before** any LLM context; tool-args constructed from typed data only; design/interview agents have no shell tools | `orchestrator/agentic_alz/llm/guard.py`, `schemas/` |
| LLM returns invalid JSON | Strict schema validation on output; halt + escalate on failure | `orchestrator/agentic_alz/llm/guard.py` |
| Runaway loop / cost blow-up | Per-stage token budget; per-tool timeout; global kill switch | `orchestrator/agentic_alz/budget.py`, `AGENTIC_ALZ_DISABLED` |
| OIDC token replay | Federated credential restricted to specific repo + branch + environment; short audience; per-environment identity | `bootstrap/phase1.sh`, `docs/phase-0-prerequisites.md` |
| Plan/apply divergence | Apply consumes immutable saved plan artifact; post-apply re-plan, drift opens issue | `.github/workflows/apply.yml` |
| `terraform destroy` abuse | CI policy blocks `destroy`; destructive-op deny-list at wrapper | `orchestrator/agentic_alz/terraform/wrapper.py`, `.github/workflows/apply.yml` |
| Privilege creep via DINE policies | Drift detector watches Owner / UAA assignments; high-priority issue | `orchestrator/agentic_alz/operate/rbac_drift.py` |
| Compromised dependency | Pinned versions in `versions.lock` and `pyproject.toml`; Dependabot; supply-chain scanning in CI | `templates/*/versions.lock`, `orchestrator/pyproject.toml` |

## Residual risks accepted in v1

- A reviewer who blindly approves PRs is the weakest link. Training and
  required reviewer rotation are organisational, not technical.
- The eval harness deploys to a real (sandbox) subscription. A bug in a
  template can spend up to the spend cap before being detected.
- Microsoft Learn MCP content is treated as advisory; if it returns a
  hallucinated URL the ADR will cite it. Reviewers are expected to verify.
