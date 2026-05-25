# Final Summary Contract: finalize-log Addendum

Status-date: 2026-05-25
Status: active governance addendum
Scope: evidence-bearing local workflow closeout after PR808

## Purpose

This addendum records the PR808 hardening rule without shortening or deleting the existing `docs/governance/FINAL_SUMMARY_CONTRACT.md` content.

The existing final summary contract remains authoritative. This addendum tightens its closeout route for evidence-bearing local workflows.

## Required closeout route

Evidence-bearing local workflow closeouts must use `agentic-kit evidence finalize-log` or a stricter successor when a terminal log is finalized for repository evidence.

The finalization route must validate the structured summary, reject invalid success semantics, reject incomplete or contradictory remote-evidence claims, print the canonical summary visibly to stdout, preserve the repo-readable log path named in the summary, and avoid replacing a failed finalization with a later handwritten success footer.

## Handwritten success footer boundary

A handwritten final success footer is not valid closeout evidence for an evidence-bearing workflow after the finalize-log route exists.

The final visible evidence anchor for a log-backed workflow is the rendered canonical summary emitted by `agentic_project_kit.run_summary_renderer`, `./ns summary`, `agentic-kit evidence finalize-log`, or a stricter successor.

If `agentic-kit evidence finalize-log` reports failure, rejects a field, rejects incomplete remote evidence, or reports invalid success semantics, the workflow must stop with a failing or pending result. A later handwritten success footer must not override that failure.

## Chat acknowledgement rule

`d`, `D`, `f`, `F`, `w`, and similar short chat signals remain communication acknowledgements only. They are not evidence.

Before continuing after such a signal, a successor chat must inspect the named `docs/reports/terminal/*.log` path directly or run `agentic-kit evidence inspect --require-summary` locally.

## Expected negative-smoke boundary

Expected negative smokes are allowed only when their failure is explicitly scoped as expected behavior and the workflow still ends with exactly one canonical final summary.

A negative smoke that prints an internal failure marker inside a log must not be left ambiguous as an unresolved workflow failure. The final summary must explain what invariant the negative smoke proved and why the surrounding workflow legitimately continued.

## PR808 evidence anchor

PR808 verified that `agentic-kit evidence finalize-log` prints the canonical summary visibly and rejects invalid success plus incomplete remote-evidence semantics without a traceback.

Current evidence anchor:

- `docs/reports/terminal/pr808-visible-finalize-summary-verify.log`
