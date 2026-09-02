# Govern an Existing Repository in 15 Minutes

Status: active
Status-date: 2026-08-14
Audience: maintainers adopting an existing Git repository

This guide is the shortest supported brownfield path for using
`agentic-project-kit` as an operating layer around an existing repository. It is
not a claim that the target repository already conforms to the Kit, DPA, release,
or documentation standards.

## 1. Install the Kit

```bash
python -m pip install "agentic-project-kit @ git+https://github.com/vfi64/agentic-project-kit.git@main"
agentic-kit --version
```

Direct PyPI installation is planned but not claimed until the PyPI package
availability claim is verified on the generated claim-evidence page.

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
`hygiene` manifest block. It appends `.agentic/tmp/` and `.agentic/rule_ack/` to
`.gitignore`. `agentic-kit transfer commit` refuses direct or broad path
selections that would stage `.agentic/rule_ack/` runtime state. It does not
modify application source files.

Older external workspaces may not yet have the `.agentic/rule_ack/` ignore line.
`agentic-kit rules acknowledge` writes a local Git exclude for that runtime path
so acknowledgement state remains available to transfer gates without creating
visible product-repository dirty state.

## 4. Run Health Gates

Use Kit gates for the operating layer:

```bash
agentic-kit check-docs --root PATH
agentic-kit check --root PATH
agentic-kit doctor --root PATH
agentic-kit governance check --root PATH
agentic-kit standard-gates-audit-suite
```

`check` and `check-docs` are error-list gates with zero/non-zero exits. `doctor`
renders a health report with `PASS`, `FAIL`, `WARN`, and `SKIP`. In external
workspace mode the standard gate suite and planning-doc slice gate use the
external operating-layer gate set; they do not run Kit self-hosting tests.
For audit evidence, run `agentic-kit check --root PATH --context` or
`agentic-kit check-docs --root PATH --json` to show whether those gates are using
the external workspace-state document set. These commands do not render
per-check statuses; `doctor` is the status renderer.

In an external manifest workspace, `SKIP` means the check is not applicable to
the target repository. For example, Kit-specific version drift remains
project-owned release governance. `WARN` remains advisory and should not be
ignored just because some checks are skipped.

Run the target project's own tests in the target project's own environment. A Kit
virtual environment is not a replacement for the product repository's runtime.

When the governed target branch is an integration branch rather than `main`,
start work with `agentic-kit work start --from-ref origin/<branch>`. The wrapper
fetches refs and creates the work branch from that ref, but it does not run the
post-merge check as a feature-branch pre-PR gate.

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

After updating the Kit package, inspect the target repository before applying
manifest changes:

```bash
python -m pip install --upgrade "agentic-project-kit @ git+https://github.com/vfi64/agentic-project-kit.git@main"
agentic-kit doctor --root PATH
```

Workspace manifest upgrades are dry-run by default:

```bash
agentic-kit workspace upgrade --root PATH
```

Use `--execute` only after reviewing the diff. The v1 to v2 migration writes a
manifest backup and materializes the `hygiene` block with documentation lifecycle
defaults.

```bash
agentic-kit workspace upgrade --root PATH --execute
agentic-kit check --root PATH
agentic-kit doctor --root PATH
```

## Current Limits

- Local brownfield adoption is tested; arbitrary unrelated repositories still
  need broader evidence.
- Remote adoption PRs and target CI interpretation remain a separate validation
  step.
- The Kit does not claim DPA or release conformance for a foreign repository
  unless a bounded, maintainer-authorized assessment says so.
