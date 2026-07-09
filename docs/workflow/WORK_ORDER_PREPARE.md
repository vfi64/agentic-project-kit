Status: active
Status-date: 2026-07-09
Superseded-by: n/a

# Work Order Prepare

Status: active
Decision status: accepted

## Purpose

`work-order prepare` turns versioned repo templates into concrete work orders. This reduces fragile chat-authored shell blocks and makes commands, gates, logs, and postconditions testable before execution.

## Rule

Routine workflows should be expressed as repo-backed work orders instead of long ad-hoc terminal blocks. Generated work orders must pass the work order contract before they are executed.
