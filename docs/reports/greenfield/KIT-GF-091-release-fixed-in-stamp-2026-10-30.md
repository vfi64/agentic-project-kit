---
artifact_type: evidence
status: active
review_policy: historical_evidence
---
# KIT-GF-091 — release assignment of finding versions

## Observed and cause

At main `1666ec6fbcd1005d275afaff5bd1de608a122b91`, the catalog still
marked KIT-GF-087/088/089/090 as unreleased and left KIT-GF-070 empty.
`prepare_release_state` updated release metadata but neither assigned catalog
versions nor called the Greenfield exporter. `release run` delegated preparation
to that path in B2; its B4 approval did not name the finding IDs. The exporter
faithfully projected the stale source values. This is a producer omission,
not an export formatting defect.

## Repair and boundary

The focused `release_greenfield_stamp` module preflights the source catalog.
Only CLOSED entries with exactly `fixed_in: unreleased` receive the target
version. Existing versions and OPEN entries stay unchanged. Empty or missing
`fixed_in` on CLOSED entries BLOCKS preparation before metadata writes: release
history cannot safely be inferred from the current release number. The error
names the IDs and requests historical evidence. Malformed catalog data retains
the existing validator's refusal.

The preparation result names selected IDs and binds them to the target version
and source catalog digest. Write mode updates the source and calls the existing
signed Greenfield export route; exported files are never patched manually.
B4 includes the prepared target-version IDs and exact catalog digest in its
approval signature, including on resume. Readiness and preparation dry-runs
remain read-only. Consumer workspaces are excluded. Category/summary checks,
publication permissions and consumer VERIFIED_FIXED authority are unchanged.

Review-only modularization exception: existing release adapters remain large;
this slice adds only delegation to the focused module. A later cohesive release
adapter extraction is the next safe modularization step, not part of this fix.
The existing typed release plan is sufficient; an additional DCO layer would
duplicate its validation and signatures.

## Historical reconciliation

All listed PRs are merged. Their merge commits are ancestors of the named local
release tags; CHANGELOG release sections independently identify the shipped work.

| Finding | fixed_in | Public evidence |
| --- | --- | --- |
| KIT-GF-070 | 1.1.6 | [PR #2607](https://github.com/vfi64/agentic-project-kit/pull/2607), merge d3f43be169fd8fa19cd9bd10e46a11f36e3e4f55; v1.1.6 bullet completing the six remaining machine contracts |
| KIT-GF-087 | 1.1.7 | [PR #2652](https://github.com/vfi64/agentic-project-kit/pull/2652), merge f475c0b512c4e787515e0e1e6fedd284b15a50ee; v1.1.7 bootstrap recovery bullet |
| KIT-GF-088 | 1.1.7 | Same PR #2652 and v1.1.7 gate-isolation bullet |
| KIT-GF-089 | 1.1.7 | [PR #2658](https://github.com/vfi64/agentic-project-kit/pull/2658), merge 02d8065173b4dd4170b59c1dc0dd15775b82ac76; v1.1.7 owned-runtime bullet |
| KIT-GF-090 | 1.1.8 | [PR #2673](https://github.com/vfi64/agentic-project-kit/pull/2673), merge 113dd252719ed863059336df7e9314c02427a9db; v1.1.8 tag-synchronization bullets |

KIT-GF-091 itself remains unreleased until a later owner-approved release. Its
synthetic machine contract deliberately starts CLOSED/unreleased and proves the
assignment through the installed release-prep CLI. It does not publish anything.

## Verification

Before implementation: all four new regression cases failed; the 34 existing
release preparation, release-run and export cases passed. After implementation:
the combined 38 cases passed. They cover dry-run, CLOSED versus OPEN assignment,
preservation of existing versions, canonical exports, idempotency, empty/missing
version refusal before writes and ID/catalog binding in the B4 signature.

Final local validation (2026-10-30):

- Full suite: `./.venv/bin/python -m pytest -q -n 4 --dist worksteal`:
  4331 passed. The full suite includes the release-content checkout audits and
  the Changelog hygiene tests; no audit or category rule was weakened.
- Ruff, check, check-docs, doctor and canonical site build: exit 0. Doctor retains
  76 report-only lifecycle findings; these are not findings closure.
- Fresh virtual environment, non-editable `pip install .`, invoked outside the
  source checkout: KIT-GF-091 PASS 1, FAIL 0. The imported Kit is under the fresh
  environment's site-packages. The candidate retains development metadata 1.1.8;
  this is not a new published build.
- Historical PRs are included in their assigned tags and absent from the
  immediately preceding release tags. No external ledger was changed.

The metadata fixture proves local planning, assignment, export and idempotency;
the independent B4 unit test proves signature binding. No live release-run or
publication acceptance is claimed. No release, tag or package publication was
performed by this slice.
