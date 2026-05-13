# Scribe — History

**Project:** Agentic ALZ — deterministic GitOps pipeline for Azure Landing Zones.
**Repo:** martinopedal/agentic-alz
**Cast at:** 2026-05-12T22:36:05Z

## Core Context

- Append-only files (decisions.md, history.md, log/, orchestration-log/) merge with the `union` driver per `.gitattributes`.
- `decisions.md` archive threshold: ~20 KB → archive entries older than 30 days to `decisions-archive.md`.
- `history.md` summarization threshold: ~12 KB.

## Learnings

(append below — newest at top)
