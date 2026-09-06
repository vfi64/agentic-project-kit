# Release 1.0.9

## Highlights

- Deterministic release notes generated from local Git tag-diff evidence.

## Added
- None.

## Changed
- None.

## Fixed
- Fix work start from integration refs (PR #2267, `134bd4e7`).
- Harden greenfield workflow closeout routing (PR #2269, `14e73fce`).
- Harden external PR lifecycle context (PR #2271, `5273ae40`).

## Governance
- Keep command-for JSON warning-free (PR #2273, `b79ff5be`).

## Transfer / Handoff
- Treat successor projections as recoverable volatile state (PR #2275, `6d41a618`).

## Docs
- Add document headroom warning budgets (PR #2263, `253ea389`).

## Tests / Gates
- Fix external workspace first-cycle gates (PR #2265, `c46606a9`).

## Release
- Record release 1.0.8 DOI and PyPI closeout (PR #2261, `792bd72b`).

## Breaking
- None.

## Administrative Handoff Refresh
- Refresh handoff state after PR2261 (PR #2262, `758797ac`).
- Refresh handoff state after PR2263 (PR #2264, `b35f755d`).
- Refresh handoff state after PR2265 (PR #2266, `9dbb93a3`).
- Refresh handoff state after PR2267 (PR #2268, `78d071b8`).
- Refresh handoff state after PR2269 (PR #2270, `f1fca7d5`).
- Refresh handoff state after PR2271 (PR #2272, `f619420e`).
- Refresh handoff state after PR2273 (PR #2274, `4bbc987a`).
- Refresh handoff state after PR2275 (PR #2276, `c2f01b21`).

## Evidence
- Range: `v1.0.8..main`.
- Generated timestamp source: `to_ref_committer_date_utc`.
- `792bd72b` PR #2261: Record release 1.0.8 DOI and PyPI closeout
- `253ea389` PR #2263: Add document headroom warning budgets
- `c46606a9` PR #2265: Fix external workspace first-cycle gates
- `134bd4e7` PR #2267: Fix work start from integration refs
- `14e73fce` PR #2269: Harden greenfield workflow closeout routing
- `5273ae40` PR #2271: Harden external PR lifecycle context
- `b79ff5be` PR #2273: Keep command-for JSON warning-free
- `6d41a618` PR #2275: Treat successor projections as recoverable volatile state
- `758797ac` PR #2262: Refresh handoff state after PR2261
- `b35f755d` PR #2264: Refresh handoff state after PR2263
- `9dbb93a3` PR #2266: Refresh handoff state after PR2265
- `78d071b8` PR #2268: Refresh handoff state after PR2267
- `f1fca7d5` PR #2270: Refresh handoff state after PR2269
- `f619420e` PR #2272: Refresh handoff state after PR2271
- `4bbc987a` PR #2274: Refresh handoff state after PR2273
- `c2f01b21` PR #2276: Refresh handoff state after PR2275

## Known Issues
- None recorded by the deterministic release-notes generator.
