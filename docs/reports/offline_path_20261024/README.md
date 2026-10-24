# Offline work and release-entry observation

Source: `7a6173cab704d57322e3ad22ddf4c02096314b1d`. Outcome: **BOUNDED_COMPLETE**.

235 CLI callback entries; 62 different commands; 102 distinct **direct** edges. These are not ancestor-closure counts.

One self-hosting fixture with synthetic history. Callback entries and fake green CI do not prove successful live publication, universal coverage, or a common kernel.

## Bounded execution

The inherited OS probes denied both network and outside-root writes with EPERM. All Git and fake-GitHub effects stayed in the owned fixture. No model, remote API, real PR, tag, release, PyPI or Zenodo publication was used.

| Step | rc | Structured verdict | Seconds |
|---|---:|---|---:|
| acknowledge | 0 | text acknowledgement | 1.912 |
| bootstrap handoff | 0 | PASS | 14.883 |
| sync main | 0 | PASS | 8.267 |
| start work | 0 | PASS | 14.55 |
| finish plan | 0 | PLANNED | 1.744 |
| finish work | 0 | PASS | 74.884 |
| sync completed work | 0 | PASS | 8.6 |
| handoff | 0 | PASS | 2.646 |
| release plan | 0 | AWAITING_APPROVAL | 87.157 |
| release B4 | 0 | AWAITING_APPROVAL | 70.337 |

B4 changes version files and handoff projections inside the synthetic fixture; the source pin names its initial code base.

Stop boundary: intentional boundary before C2 publication approval; B4-only release observation.

Callback entries include plans and dry runs; command names alone do not identify remote effects. The release track stops before C2 publication approval. This is a work/prepare/closeout observation, not the complete publication path. G0 shows direct callees for selected entrypoints; G2/G3 remain separate current contract views.

## Reproduction and preserved limits

Run the pinned developer runner into a fresh owned temporary directory, then use `scripts/offline_path/export.py` to reproduce the bounded public projection. Process IDs, synthetic Git commit times and durations vary. Callback receipts and source/runner hashes are retained; no byte-identical runtime timing is promised.

The historical 2026-10-15 simulation also included inferred core ownership and ancestor relationships. Its 301 pairs are not this report's direct-edge denominator. Static analysis remains incomplete and its `*parts` extension stays deferred to D1.

Development preflights were preserved locally: the first dependency lookup chose an old site-packages directory; initial tracing was displaced by system sitecustomize; a missing fixture tag caused release readiness to block. These were runner/fixture defects, not evidence of Kit product defects. The final runner uses the current interpreter path, an explicit .pth import, a version tag and trace-integrity checks.

See `docs/reference/OFFLINE_PATH_OBSERVATION.md` and the two regression modules. No historical audit was overwritten.
