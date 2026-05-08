# Lab mode

> **Lab mode is a development crutch, not a production path.** Anything
> deployed via lab mode is a throw-away sandbox. The production pipeline
> (Phase 0 prerequisites → bootstrap → validate → plan → apply) is
> unchanged and remains the only supported way to land an ALZ in a real
> environment.

The official ALZ Accelerator is a great target shape; getting from a
clean tenant to a working hub-and-spoke ALZ is still slow. Lab mode is
the shortcut for **architects building demo / training / experiment
sandboxes** in a single subscription. It produces a self-contained
Terraform working directory and stops there — the operator runs
`terraform apply` themselves, on their own machine, against their own
sandbox.

## What lab mode is

`agentic-alz lab init` takes one `inputs.yaml` and emits a
`lab-bundle.tar.gz` containing:

- The full hub-and-spoke template (`main.tf`, `providers.tf`,
  `variables.tf`, `outputs.tf`, `versions.lock`, `.tflint.hcl`).
- A `terraform.tfvars.json` derived from your inputs.
- A `lab-manifest.json` with the rendered topology, the `inputs_sha256`,
  and the list of files for traceability.

Crucially, the production `backend.tf` is **stripped** from the bundle.
Lab mode runs against **local Terraform state by default** so you can
spin up and tear down without provisioning the hardened storage account
described in [`docs/phase-0-prerequisites.md`](phase-0-prerequisites.md).

## What lab mode is **not**

- It is **not** an apply path. The CLI never runs `terraform apply`.
- It is **not** an LLM action. The Interview stage is separate; you can
  hand-write `inputs.yaml` and skip it.
- It is **not** a way to ship to a production sub. The CLI refuses any
  inputs whose `tags.defaults.Environment` is not `"sandbox"`.

## Trimmed prerequisites (lab only)

Lab mode is opinionated about minimums. You need:

1. One Azure subscription you own and are willing to wipe. **Use the
   same `subscription_id` for `management`, `connectivity`, and
   `identity` in `platform_subscriptions`** — see
   [`evals/golden/lab-hns/inputs.yaml`](../evals/golden/lab-hns/inputs.yaml).
2. `terraform` ≥ 1.5 and `az` on PATH. No state account needed for the
   lab — see the red banner below.
3. Owner or Contributor + User Access Administrator on the sub for the
   AAD identity Terraform will use.

Everything else from Phase 0 (hardened state SA, federated identities,
sibling repos, CODEOWNERs) is **deferred to the production path**.

## Quick start

```bash
# 1. Hand-edit a lab inputs file or use the golden one.
cp evals/golden/lab-hns/inputs.yaml my-lab.yaml
# Edit subscription_id, tenant_id, hub address space, etc.

# 2. Render the bundle. CLI refuses non-sandbox inputs.
agentic-alz lab init --inputs my-lab.yaml --out /tmp/lab-bundle.tar.gz

# 3. Unpack and apply yourself, out of band.
mkdir /tmp/lab && tar -xzf /tmp/lab-bundle.tar.gz -C /tmp/lab
cd /tmp/lab
terraform init           # local state, no backend.tf
terraform validate
terraform plan -out tfplan
terraform apply tfplan   # YOU run this. The CLI does not.
```

## ⚠️ Red banner: local Terraform state

> Lab bundles use the implicit local backend. Local state is fine for
> ephemeral labs. **Never** use a lab bundle against a production-shaped
> subscription, never share the resulting `terraform.tfstate` (it
> contains secrets), and tear the lab down with
> `terraform destroy` before you walk away. If you find yourself wanting
> to reuse a lab, stop — promote the inputs to a non-sandbox
> `Environment` tag and go through the real pipeline instead.

## How lab mode interacts with the rest of the repo

- It runs the same generator (`stages/generate.py`) as production, so
  the rendered Terraform passes the same `avm_pinning.rego` and
  `naming.rego` policies.
- It does **not** run the OPA policies as part of `lab init` — the
  operator is encouraged to run `conftest test ...` themselves on the
  unpacked bundle. (Future work: optional `--with-policy-check` flag.)
- The kill switch (`AGENTIC_ALZ_DISABLED`) short-circuits `lab init`
  exactly the same way it short-circuits every other CLI command.
