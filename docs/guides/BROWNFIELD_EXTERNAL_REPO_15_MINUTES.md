# Govern an Existing Repository in 15 Minutes

Status: active
Status-date: 2026-08-13
Audience: maintainers adopting an existing Git repository

This guide is the shortest supported brownfield path for using
`agentic-project-kit` as an operating layer around an existing repository. It is
not a claim that the target repository already conforms to the Kit, DPA, release,
or documentation standards.

## 1. Install the Kit

```bash
pip install agentic-project-kit
agentic-kit --version
```

For local development of the Kit itself, use the repository virtual environment
instead of a global install.

## 2. Inspect Before Writing

Run the read-only intake commands from outside or inside the target repository:

```bash
agentic-kit workspace dpa-intake --root PATH
agentic-kit workspace adopt --root PATH
agentic-kit dpa repo-adoption-assessment --root PATH
```

These commands inventory the repository, propose a workspace manifest, and keep
`external_repo_conformance_claimed=false`. They do not rewrite project files and
do not perform production migration.

## 3. Initialize the Operating Layer

First inspect the plan:

```bash
agentic-kit workspace init --root PATH
```

Then write only the bounded Kit workspace files:

```bash
agentic-kit workspace init --root PATH --execute
```

The write step creates `.agentic/config.yaml`, `.agentic/state/`,
`.agentic/registries/`, transfer prompt files, CI/pre-commit templates, and a
`hygiene` manifest block. It appends `.agentic/tmp/` to `.gitignore`. It does not
modify application source files.

## 4. Run Health Gates

Use Kit gates for the operating layer:

```bash
agentic-kit check-docs --root PATH
agentic-kit check --root PATH
agentic-kit doctor --root PATH
```

`check` and `check-docs` are error-list gates with zero/non-zero exits. `doctor`
renders a health report with `PASS`, `FAIL`, `WARN`, and `SKIP`.

In an external manifest workspace, `SKIP` means the check is not applicable to
the target repository. For example, Kit-specific version drift remains
project-owned release governance. `WARN` remains advisory and should not be
ignored just because some checks are skipped.

Run the target project's own tests in the target project's own environment. A Kit
virtual environment is not a replacement for the product repository's runtime.

## 5. Produce a Handoff

Before switching chats or delegating continuation, create the deterministic
successor package:

```bash
cd PATH
agentic-kit transfer chat-switch-complete --render-prompt
```

External workspace packages are written under
`.agentic/state/handoff/packages/latest/`. Continue only when the validation
report is `PASS`.

## 6. Roll Back the Kit Layer

Inspect rollback first:

```bash
agentic-kit workspace remove --root PATH
```

Then remove exact Kit-generated files:

```bash
agentic-kit workspace remove --root PATH --execute
```

Generated successor handoff package files are recognized by signature. Unknown
or modified `.agentic/` paths block removal. Application files and project
documentation are preserved.

## 7. Upgrade the Workspace Manifest

Workspace manifest upgrades are dry-run by default:

```bash
agentic-kit workspace upgrade --root PATH
```

Use `--execute` only after reviewing the diff. The v1 to v2 migration writes a
manifest backup and materializes the `hygiene` block with documentation lifecycle
defaults.

## Current Limits

- Local brownfield adoption is tested; arbitrary unrelated repositories still
  need broader evidence.
- Remote adoption PRs and target CI interpretation remain a separate validation
  step.
- The Kit does not claim DPA or release conformance for a foreign repository
  unless a bounded, maintainer-authorized assessment says so.
