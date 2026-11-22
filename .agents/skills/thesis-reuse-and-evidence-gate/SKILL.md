---
name: thesis-reuse-and-evidence-gate
description: >
  Apply before any coding, data-processing, geospatial UI, testing or
  API-integration change in the public thesis repository. Prioritize mature
  upstream components, minimal adapters, safe preservation and scientific truth.
license: MIT
---

# Thesis reuse and evidence gate

Inspired by the **MIT-licensed, reviewed** [canonical Ponytail skill](https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail/SKILL.md) (Dietrich Gebert). This is an original, repository-local academic adaptation, **not** an installation of that package or its execution hooks.

Before editing:
1. Read root `AGENTS.md`, the touched caller and current baseline SHA.
2. Ask: **Does this feature need to exist for thesis validity or required coursework?** If not, defer.
3. Reuse existing repository functionality; then Python standard library; then currently installed upstream package; then a license-reviewed maintained package; only then write the **smallest necessary domain-specific adapter**.
4. Check upstream LICENSE/NOTICE plus data/asset terms; pin versions where installed. Do not blindly copy web code or tests.
5. Preserve main, prior V2/V3/V4, shelves, old experiments and rollback. Experimental routes only.
6. On real scientific outputs, demand original scene IDs, acquisition time, processing baseline and radiometric conversion, real raster validation, SCL/QA, source checksum and independent event-label status. **Fail closed**—never silently fallback to synthetic.
7. Unit tests should exercise **our small integration contract**; rely on upstream test suites for upstream internals. Never mistake passing tests for empirical validation.
8. Separate public satellite work from private Rota Única and assessed university projects.
9. Do not send messages, submissions, applications or restricted data; do not spend money or call optional paid APIs.

Review gate: identify the reused library/version, integration proof, input provenance, explicit limitations, actual commands/output, preservation reference and any untested behavior. A reviewed design does not equal independently reproduced science.

Optional skills after source/security review: [Grafana Skills](https://github.com/grafana/skills) for observability when a real backend exists; [OpenRouter Skills](https://github.com/OpenRouterTeam/skills) only for explicitly approved zero-spend external-agent workflows. **Neither is required or active in the static Pages demonstration.**
