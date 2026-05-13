# Ceremonies

The Coordinator checks `before` triggers prior to spawning a work batch and `after` triggers when a batch completes. Manual ceremonies run only when the user asks.

## Sensitive-path huddle

- **Trigger:** `before`, when the work batch will write into any sensitive path listed in `routing.md`
- **Facilitator:** Holden
- **Participants:** Holden + the domain owner of the path + Bobbie (if NetSec-relevant)
- **Goal:** Confirm the matching playbook (`docs/playbooks/0X-*.md`) is selected, the rubberduck plan is in scope, and a multi-model judge is required.

## Multi-model judge dry-run

- **Trigger:** manual ("run the judge", "consensus check")
- **Facilitator:** Holden
- **Participants:** Holden + the author of the change
- **Goal:** Walk the rubric in `docs/multi-model-judge.md`, identify which models will vote, capture the rationale before invoking real votes.

## Post-merge retro

- **Trigger:** manual ("retro", "post-merge")
- **Facilitator:** Holden
- **Participants:** Squad members who touched the merged PR
- **Goal:** Capture lessons in decisions inbox; update playbooks if a recurring gap was found.
