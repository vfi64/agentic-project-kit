# KIT-GF-050 B — fallback handoff path in external workspaces

- Handoff-state loading resolves the active workspace path while preserving legacy layout.
- Missing handoff state is handled as an explicit skip with the expected workspace path.
- Admin-refresh failure paths clean back to the starting main branch or name the cleanup route.
- Follow-up CI PENDING classification uses structured result status, not rendered TIMEOUT text.
- Regression coverage includes namespace state, missing state, fallback cleanup, and unrelated timeout text.
