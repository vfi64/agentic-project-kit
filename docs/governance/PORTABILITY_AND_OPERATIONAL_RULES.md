Status: active
Status-date: 2026-07-09
Superseded-by: n/a

# Portability and Operational Rules

This document contains durable operational rules that are too detailed for `AGENTS.md` but still binding for repository work.

## Portable-first rule

Unless a user explicitly requires a specific operating system, new operational behavior must be implemented in importable Python core modules with argument-vector execution.

Shell scripts are compatibility shims only. They must not contain core workflow logic.

## Release and GUI baseline consequence

Before the GUI baseline is called complete, operational control surfaces must be callable through portable Python entry points. Remaining shell files must be either removed, replaced by Python entry points, or explicitly allowlisted as temporary compatibility shims by a tested portability gate.

## Failure summary rule

Final summaries must not report PASS when any hard gate in the same slice failed. A recovery slice may report PASS only when its stated recovery objective is completed and the unresolved upstream failure is explicitly named as remaining work.
