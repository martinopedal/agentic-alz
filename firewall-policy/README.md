# alz-firewall-policy (sibling-repo shape)

This directory illustrates the **shape** of the sibling
`alz-firewall-policy` repo. In production it lives in its own GitHub repo
with its own Terraform state container, NetSec CODEOWNER on `policies/base/`
and `lib/`, and branch protection requiring NetSec review.

The federated library model:

- `policies/base/` — baseline Rule Collection Groups deployed once at
  bootstrap. Vetted by NetSec. Workloads MUST NOT modify these.
- `lib/` — versioned, pre-approved RCG modules workloads consume by
  reference. Adding a new lib RCG requires one NetSec review; consuming an
  existing one does not.

The Firewall Change Composer LLM stage (deferred from v1) proposes new
`lib/` entries as PRs against this repo. It never pushes to `main`.

## Why a separate repo with separate state?

- Smaller blast radius: a mistake in firewall rules cannot rewrite the
  platform's network topology, and vice versa.
- Independent ownership: NetSec gates rule changes without becoming a
  bottleneck on platform changes.
- Independent lifecycle: rule churn is much higher than platform churn.
