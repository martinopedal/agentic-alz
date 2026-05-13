# Routing

| Signal / path / topic | Route to |
|-----------------------|----------|
| `AGENTS.md`, `docs/playbooks/`, `docs/consensus-plan.md`, ADRs | 🏗️ Holden |
| Multi-model judge calls, frontier-model allowlist (`docs/models.allowlist.yaml`) | 🏗️ Holden |
| Sensitive-path triage, CODEOWNERS, branch-protection questions | 🏗️ Holden |
| `orchestrator/agentic_alz/**`, killswitch, llm/, mcp/, terraform wrapper | 🔧 Naomi |
| `orchestrator/tests/**` (functional pytest) | 🔧 Naomi |
| `prompts/**`, `schemas/**` | 🔧 Naomi (with 🏗️ Holden review for multi-model judge) |
| Click CLI surface, `docs/generated/cli.md` | 🔧 Naomi |
| `templates/**` (Terraform / AVM), `versions.lock`, `bootstrap/` | ⚙️ Amos |
| `policies/**` (OPA Rego), conftest runs | ⚙️ Amos |
| `.github/workflows/**` (esp. `apply.yml`, `copilot-setup-steps.yml`) | ⚙️ Amos (with 🏗️ Holden + 🔒 Bobbie review for sensitive workflows) |
| `firewall-policy/**`, `alz-firewall-policy`, RCG schema | 🔒 Bobbie |
| MCP `mode: write` proposals, `docs/mcp.allowlist.yaml` write-mode entries | 🔒 Bobbie (NetSec CODEOWNER) |
| `evals/`, `evals/replay.py`, `scripts/gen_docs.py --check` | 🧪 Alex |
| ruff, lint-instructions, schema validation, CI red/green diagnosis | 🧪 Alex |
| Cross-cutting test coverage, regression hunting | 🧪 Alex |
| Multi-domain "team" question | Holden + 1–2 specialists in parallel |
| Session logs, decision merge, history maintenance | 📋 Scribe |
| Issue queue / PR backlog / CI watch | 🔄 Ralph |

## Sensitive paths (abort writes; suggest playbook)

These match `AGENTS.md` § "Sensitive paths" — agents must abort direct writes and route to a human author via the matching playbook in `docs/playbooks/`:

- `.github/workflows/apply.yml`, protected `prod` env → `08-ci-workflow-change.md`
- `bootstrap/` → `08-ci-workflow-change.md`
- `policies/` → `05-policy-change.md`
- `prompts/`, `prompts/system/`, `schemas/` → `04-prompt-or-schema-change.md`
- `docs/models.allowlist.yaml`, `docs/mcp.allowlist.yaml` → `04-prompt-or-schema-change.md`
- `.github/workflows/*.yml` (esp. apply, copilot-setup-steps, squad) → `08-ci-workflow-change.md`
- `templates/**` → `06-iac-template-change.md`
- `firewall-policy/**` and `alz-firewall-policy` → `07-firewall-lib-exemplar.md`
- `orchestrator/agentic_alz/llm/`, `orchestrator/agentic_alz/mcp/` → runtime enforcement points; treat as sensitive
