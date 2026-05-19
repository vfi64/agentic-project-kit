## Final summary contract

Every relevant workflow block must end with the framed SUMMARY contract. This contract is durable and must not disappear across chats, handoffs, or command-generation paths.

Required block:

```text
================================================================
SUMMARY
WORK RESULT: PASS|FAIL|PENDING|HARD-FAIL|NO-COMMAND
EVIDENCE RESULT: PASS|FAIL|PARTIAL|CHAT_ONLY|NOT_REQUIRED
OVERALL RESULT: PASS|FAIL|PENDING|HARD-FAIL|NO-COMMAND
REMOTE_EVIDENCE: PASS|FAIL|PARTIAL|NOT_REQUIRED
terminal_log=<repo-path-or-NONE>
command_report=<repo-path-or-NONE>
NEXT_CHAT_REPLY: p|paste-output|ask-agent-to-queue-command|continue|stop
### RESULT: PASS|FAIL|PENDING|HARD-FAIL|NO-COMMAND ###
================================================================
```

This is the preferred end marker for agent-directed terminal blocks, remote command reports, release work, merge verification, and handoff-sensitive work. Short local experiments may use a smaller marker, but any state-changing or evidence-bearing workflow must use the framed SUMMARY.

