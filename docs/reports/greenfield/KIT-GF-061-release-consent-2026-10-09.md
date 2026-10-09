# KIT-GF-061 — Attributed release consent

Source: vfi64/agp-Cockpit, docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json,
main commit `afea4be654b5bed910754d05273d18afae79e2f7`, read-only on 2026-10-09.

## Finding and repair

Release run had signatures but no declared approval policy or consent provenance.
The focused release_run_approval module implements release.approval per_gate and
upfront. Explicit policy execution requires approved-by and consent-source.
Upfront consent signs the B4 subject plus version, tag, branches, summaries,
publication policy and workflow. Matching later gates use that persisted consent;
plan or target commit drift blocks. Only successful B4 Kit merge and handoff
advances the pinned target commit. D2R always needs separate signed approval.
FAIL/BLOCKED returns immediately. State writes are atomic; each gate approval
and permitted commit transition is recorded in state/results and the release log.
CLI changes are additive; the existing remote-effect classification still applies.

## Regression

`tests/test_release_consent_dispatch.py` uses disposable external workspace
manifests and fake subprocess observations. It verifies one upfront approval
through all matching gates; attribution in evidence; missing identity/source;
wrong signatures; version, tag, policy, workflow and commit drift; and individual
per-gate stopping. CLI tests cover option forwarding and pure JSON failure output.

## Risks and expected external retest

Attribution is caller-supplied evidence, not authenticated identity or a permission
system. This preserves the architecture's single-maintainer boundary. Legacy
callers without an explicit policy remain per-gate compatible with attribution
marked unspecified. Explicit policies require attribution. No interactive prompt,
new release logic or autonomous recovery from failure is introduced.
Retest upfront and per_gate with the released Kit in a disposable Cockpit clone;
review the consent reference and ensure changed subjects block publication.
No Cockpit ledger was changed; VERIFIED_FIXED remains a workspace decision.

Command manifest ACK: `COMMAND_MANIFEST_ACK e272fbfc980c`. The release-run
remote effects remain merge, pull_request, push and release_publish.

## Slice validation

Full local suite: 3224 passed, 506 existing warnings. Final focused regressions:
75 passed. Ruff, check-docs and doctor PASS; doctor has report-only lifecycle
warnings. Generated command manifest, entrypoints, site and documentation registry
were reconciled. Remote CI and merge identifiers are reported by the Kit closeout.
