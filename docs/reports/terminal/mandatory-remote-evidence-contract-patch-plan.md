# Mandatory remote evidence contract patch plan

Goal: remove user uncertainty about whether terminal output must be copied into chat.

Required behavior:
- Every long/relevant runner must start durable logging before doing work.
- No runner may keep writing to a committed log after the commit intended to preserve that log.
- Final summaries must include REMOTE_EVIDENCE: PASS, FAIL_OR_UNKNOWN, or NOT_APPLICABLE.
- If REMOTE_EVIDENCE: PASS, the user should reply only p; no terminal paste needed.
- If REMOTE_EVIDENCE is not PASS, the footer must explicitly ask for f plus pasted output or point to a local log path.
- Interactive terminal blocks must not end with exit in a way that closes the user session.

Likely patch targets:
- src/agentic_project_kit/agent_command_runner.py
- src/agentic_project_kit/terminal_logging.py
- ./ns
- tests/test_agent_command_runner.py
- tests/test_terminal_logging.py
- tests/test_no_copy_terminal_policy.py
