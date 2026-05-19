# Compiled Agent Context

Status: active
Decision status: accepted
Review policy: update whenever durable workflow rules change

This document defines the human-facing contract for `.agentic/compiled_agent_context.yaml`.

The compiled YAML is a compact, machine-readable companion to the human governance docs. It does not replace the docs; it prevents slow, lossy reconstruction of active rules from scattered prose.

Every durable rule must be maintained in three places: human documentation, `.agentic/compiled_agent_context.yaml`, and deterministic tests.

The remote-first no-guess rule remains first: inspect the remote repository, authoritative files, and command help before acting on repository state or command syntax.
