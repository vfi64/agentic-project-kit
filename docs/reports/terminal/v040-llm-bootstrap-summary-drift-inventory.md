# LLM Bootstrap and Summary Drift Inventory

## Scope

Read-only inventory for LLM-optimized chat bootstrap, final summary rendering, drift detection, and handoff behavior. This report intentionally makes no product-code changes.

## Authoritative files inspected

- `docs/governance/FINAL_SUMMARY_CONTRACT.md`
- `docs/TEST_GATES.md`
- `docs/handoff/CURRENT_HANDOFF.md`
- `docs/STATUS.md`
- `docs/DOCUMENTATION_COVERAGE.yaml`
- `.agentic/compiled_agent_context.yaml`
- `.agentic/handoff_state.yaml`
- `src/agentic_project_kit/run_summary_renderer.py`
- `src/agentic_project_kit/final_summary_contract.py`
- `tests/test_run_summary_renderer.py`
- `tests/test_final_summary_contract.py`

## Normative target for large LLMs

A successor chat must not infer rules from memory. It must first read the authoritative bootstrap list, then run or inspect the deterministic drift check before producing any mutation terminal block. The final summary must be rendered through `./ns summary` or `agentic_project_kit.run_summary_renderer`; handwritten legacy summary fallbacks are not allowed for new workflow blocks.

## Required next implementation changes

1. Align `run_summary_renderer.py` with `docs/governance/FINAL_SUMMARY_CONTRACT.md`.
2. Extend renderer tests for `NO-COMMAND`, forbidden `REMOTE_EVIDENCE` values, terminal-log honesty, and precise validation messages.
3. Add an LLM bootstrap and drift contract document that lists mandatory sources, forbidden autonomy, drift classes, and drift reaction.
4. Add a deterministic communication-rules drift check and expose it through CLI/`./ns` or integrate it into governance-check.
5. Update compiled context and documentation coverage so the rules survive chat handoff and repo drift.
6. Add or extend a handoff-prompt path that emits a comprehensive successor-chat prompt when drift is detected.

## Known drift risks to eliminate

- `REMOTE_EVIDENCE: PENDING` must not be generated as a final summary value.
- `REMOTE_EVIDENCE: NONE` and `REMOTE_EVIDENCE: CHAT_ONLY` must not pass as final remote-evidence states.
- `NO-COMMAND` must be consistently supported where the contract declares it.
- New runbooks must not use `{ ... } | tee "$LOG"` as the mechanism that controls final PASS/FAIL state.
- New runbooks must not append handwritten result footers after `./ns summary`.
- A pushed evidence log may prove a failed run; it must not relabel failed work as successful.

## Proposed LLM optimization model

Use a three-layer model: short bootstrap instruction, machine-readable compiled context, and deterministic drift check. Do not rely on long prompts alone. The LLM must be forced into a fixed startup sequence: read sources, check drift, summarize current constraints, then act. If drift is detected, stop mutation and offer a handoff prompt.
