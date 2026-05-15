# Hidden autopilot

## Kind

anti-pattern

## Risk

Automation silently changes workflow state, architecture direction, or review outcomes without explicit human review.

## Avoid when

- A command would turn advisory output into a gate.
- A helper would choose architecture or project direction automatically.
- A workflow step would hide state changes from the user.

## Safer alternative

Keep automation explicit, bounded, and reviewable. Advisory output should remain advisory unless a separate deterministic gate is intentionally designed and documented.
