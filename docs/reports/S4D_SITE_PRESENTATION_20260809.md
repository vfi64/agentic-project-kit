# S4d Site Presentation Layer

Date: 2026-08-09

Base before S4d: `30de3c23b02a8dabdac6ea21d542b81fe38dc8d6`
(`Refresh handoff state after PR2035 (#2036)`).

## Scope

S4d turns the generated website from a minimal repository projection into a more
legible public project page. It does not add a new technical truth source.

## Implemented Presentation

- Homepage sections now cover Repository Memory, Runtime Structure, CLI, GUI,
  Communication, and Claims.
- `static/runtime-map.svg` is a technical visual showing repository sources
  flowing into the deterministic site builder and generated public projections.
- Guided lifecycle examples are generated from `surface: orchestrator`.
- Common blocker diagnostics reuse the existing GUI command projection instead
  of introducing a website-specific taxonomy.
- Status boards render computed claim categories: verified now, available but
  evolving, planned, and not claimed.

## Boundaries

- Technical facts remain generated from repository sources or computed evidence.
- `not claimed` remains a curated boundary for public overclaim prevention.
- GitHub Pages live publication remains pending repository Pages source
  configuration even though the build/deploy workflow is ready and current
  Pages runs are green.
