# Terminal safety governance

This document records the durable guardrails for terminal command blocks used in
LLM-to-terminal workflows. The goal is to prevent the recurring standard errors
that caused hung shells or false local gate failures.

## Required invariants

- `ruff-python-only`: local feature gates must run Ruff only on Python paths,
  currently `src` and `tests`. Shell files must be checked with `sh -n`, not
  with Ruff.
- `terminal-quote-safety`: generated terminal blocks must avoid constructs that
  commonly leave the shell at prompts such as `quote>`, `dquote>`, or
  `heredoc>`.
- Heredocs are forbidden in generated terminal blocks. Prefer existing scripts
  or generated helper files.
- Risky multiline `python -c` snippets are forbidden in generated terminal
  blocks. Prefer module entry points, short one-liners without embedded
  newlines, or checked helper scripts.
- Unquoted regex or glob tokens such as `[0-9]+` must not appear in generated
  shell commands. Quote them explicitly.
- Terminal blocks must not end the user's interactive shell with `exit` or
  `exec`.

## Enforcement

The structural terminal guard lives in
`src/agentic_project_kit/terminal_block_guard.py` and is covered by
`tests/test_terminal_block_guard.py`.

The local gate Ruff target contract is covered by
`tests/test_local_feature_gate_contract.py` and
`tests/test_v034_local_feature_gate_core.py`.

This governance note is intentionally short: it documents the policy, while the
Python tests make the policy machine-checkable.
