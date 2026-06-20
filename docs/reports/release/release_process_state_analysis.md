# Release Process State Analysis

- schema_version: 1
- kind: release_process_state_analysis
- minimal_status_command: `agentic-kit release-status --json`

## Summary

The release process has distinct lifecycle states. The important conceptual fix is to keep `prepared` separate from `current_verified`. A version can be prepared in package metadata while the previous version remains the current verified release until tag/GitHub release publication, Zenodo DOI verification, DOI closeout, merge and final handoff are complete.

## State Matrix

| State | Meaning | Next Safe Commands |
| --- | --- | --- |
| planned | Target version selected; metadata may still be previous release | `release-plan`, `release-preflight`, `release-prep --dry-run` |
| prepared | Metadata anchors contain target version, no live publish guarantee yet | `release-check`, `release-publish --dry-run`, authority gate |
| published | Tag/GitHub release exist, DOI may still propagate | `post-release-check --version X` |
| doi_verified | Zenodo version DOI verified by post-release-check | `post-release-doi-closeout --write --json` |
| closed_out | Expected DOI closeout files updated atomically | tests, audits, protected-diff-plan, PR/merge |
| current_verified | Main is clean, handoff fresh, release fully closed out | next planning slice may proceed |

## Design Decision

Add a read-only local status command first:

```bash
agentic-kit release-status --json
```

It reads release anchor files and local tag state, reports blockers/warnings, and does not perform remote release checks or mutate files. Remote checks remain delegated to `post-release-check`; writes remain delegated to `release-prep`, `release-publish`, and `post-release-doi-closeout`.

## Known Brüche / Risiken

- `release-publish` can encounter transient GitHub/Zenodo visibility immediately after creating a release. This should be handled by bounded polling/retry in a later hardening slice.
- Manual DOI or metadata edits remain forbidden; the state model is read-only and cannot justify bypassing authority gates.
- Release notes should bind to this lifecycle after the release-notes generator MVP exists.

See `release_process_state_analysis.json` for the machine-readable matrix.
