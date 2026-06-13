# NS-to-agentic-kit migration plan

Source audit:
- `docs/reports/ns-migration/ns_to_agentic_kit_audit.md`
- `docs/reports/ns-migration/ns_to_agentic_kit_inventory.json`

Required order:
1. Complete `./ns` replacement/deprecation slices.
2. Verify command reference and protected-change gates.
3. Start GUI only after active workflows no longer depend primarily on `./ns`.

Initial work packages:
- Classify references.
- Build replacement table.
- Implement missing `agentic-kit` wrappers.
- Update active docs minimally.
- Keep legacy compatibility notes explicitly labeled.
