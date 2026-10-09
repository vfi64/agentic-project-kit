# KIT-GF-049 — Generated reference does not declare Kit self-hosting

Source: vfi64/agp-Cockpit, docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json,
main commit `afea4be654b5bed910754d05273d18afae79e2f7`, read-only on 2026-10-09.

## Confirmed remaining defect

The 2026-10-07 fix was incomplete: commands sync-entrypoints writes a command
reference into adopting workspaces too. Presence of that projection wrongly
enabled transfer command-reference-check, which invokes a Kit-repository test.
The Cockpit ledger reproduces this on released Kit 1.0.20.

## Repair and regression

Automatic command-reference-check selection now requires a Kit development
checkout. An external workspace may explicitly opt in via release.publish_checks;
a generated reference alone does not opt in. Documentation registry presence
continues to enable docs-audit and preserve failure blocking. SKIP stays outside
blockers and the publish approval signature. No route or remote effect changes.
The existing external publication test now includes the generated JSON reference
and verifies both checks SKIP; registry blocking and explicit opt-in tests remain.

## Expected external retest

In a disposable Cockpit clone with publication github, remove the temporary
publish_checks override and retain its generated command reference. Both Kit-only
checks must SKIP. A declared documentation registry still enables docs-audit.
This supersedes the older report's generated-reference auto-detection claim.
No Cockpit ledger was changed; VERIFIED_FIXED remains a workspace decision.

## Slice validation

Full local suite: 3224 passed, 506 existing warnings. Final focused regressions:
75 passed. Ruff, check-docs and doctor PASS; doctor has report-only lifecycle
warnings. Generated command manifest, entrypoints, site and documentation registry
were reconciled. Remote CI and merge identifiers are reported by the Kit closeout.
