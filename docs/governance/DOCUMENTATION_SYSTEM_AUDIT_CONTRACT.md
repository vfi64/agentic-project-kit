# Documentation System Audit Contract

Status: active governance contract

`agentic-kit docs-audit` is the umbrella documentation-system audit. It reports six dimensions in order:

1. Aktualität
2. Vollständigkeit
3. Korrektheit
4. Redundanzfreiheit
5. Stringenz der Dokumentenordnung
6. Konsistenz

The command aggregates deterministic findings from existing documentation checks and names review-only boundaries where full semantic proof is not possible.

Required command:

```bash
agentic-kit docs-audit
```

Optional report:

```bash
agentic-kit docs-audit --report docs-audit.json
```

Successor chats must preserve this source order:

1. `.agentic/compiled_agent_context.yaml`
2. `docs/governance/FINAL_SUMMARY_CONTRACT.md`
3. `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`
4. `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`
5. `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`
6. `docs/TEST_GATES.md`
7. `docs/STATUS.md`
8. `docs/handoff/CURRENT_HANDOFF.md`
