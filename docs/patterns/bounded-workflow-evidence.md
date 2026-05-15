# Bounded workflow evidence

## Kind

pattern

## Intent

Capture bounded local workflow output as reviewable evidence instead of pasting long terminal logs.

## Use when

- A local workflow produces test, lint, documentation, or doctor output.
- The output is useful for review but too long or fragile for chat copy-and-paste.
- The repository should remain the source of truth for the current project state.

## Keep non-binding

This pattern preserves evidence for review. It must not automatically approve a change, merge code, or override human judgment.
