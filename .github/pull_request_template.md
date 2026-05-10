## Summary

- 

## Architecture Contract Check

Read `docs/architecture/ARCHITECTURE_CONTRACT.md` before submitting this PR.

- [ ] Not architecture-relevant; no contract update needed.
- [ ] Architecture-relevant; contract reviewed and still valid.
- [ ] Architecture-relevant; contract updated in this PR.

If architecture-relevant, explain the impact:

- 

## Evidence

Required local gate:

```bash
git status --short
git branch --show-current
python -m pytest -q
ruff check .
agentic-kit check-docs
agentic-kit doctor
```

Results:

- `python -m pytest -q`:
- `ruff check .`:
- `agentic-kit check-docs`:
- `agentic-kit doctor`:

## Reviewability

- Intended outcome:
- Changed files:
- Tests run:
- Tests not run:
- Remaining risks:
- Next safe step:
