# KIT-GF-023 — Pure JSON stdout through transfer stop paths

Source: vfi64/agp-Cockpit, main commit
`f92361ad3c4bcdf93c4d38a350bddcf09f5e4f95`, ledger
`docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json`, read-only on 2026-10-09.

## Finding and repair

Several capability-gated transfer commands failed to forward their JSON flag to
the shared rules gate, which appended FINAL_SIGNAL/FINAL_NEXT/CHAT_REPLY text
after JSON on rejection. All such callers now forward the output mode explicitly.
Normal lifecycle JSON emitters already emitted one document and remain unchanged.

Early runner, order-loader, report-reader, closeout and remote-next error handlers
also emitted plain text. They now return one structured error document in JSON
mode with status, returncode, error and next action. Error payload construction
lives in `cli_error_payload.py`; CLI adapters render it. Existing text output,
capability enforcement, exit codes, actions and approval requirements are retained.
Framework-level syntax errors still use the framework's stderr diagnostics.

## Regression and external retest

`tests/test_transfer_json_contract.py` runs real CLI commands in disposable external
manifest workspaces, with a generated-reference location and no Kit documents.
It covers ten guarded command paths, seven early-input/report failures, two
runtime stop paths and JSON escaping. A caller-inventory test prevents new JSON
capability callers from dropping the flag. Existing transfer/lifecycle tests cover
normal results and text-mode behavior. The focused suite passes 246 tests.

An installed-wheel external smoke test checks success and blocked/error results
with unmodified `json.loads(stdout)`. Full-suite and gate results are recorded in
the final closeout reply. The manifest/reference are regenerated; existing remote
effect classifications are unchanged. ACK: `d75e2e2a30bd`.

Expected Cockpit retest: invoke the affected transfer routes with `--json` on
missing acknowledgement/input and normal lifecycle results, and parse the full
stdout directly. GF-027 output-size and red-CI return-code changes are excluded.
No Cockpit ledger, release tag or publication is changed; VERIFIED_FIXED belongs
to the workspace after its released-package retest.

## Scope and risk

The remaining risk is a consumer that relied on plain text despite requesting
JSON; it must now read the structured error. No command executes additional
steps. Existing split transfer adapters retain their responsibilities; the shared
error renderer is small and delegates data construction to an importable module.
No new workflow state or DCO layer is needed for a single result document.
