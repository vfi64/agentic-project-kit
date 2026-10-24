Status: active
Status-date: 2026-10-24
Superseded-by: n/a

# Bounded offline path observation and generated figures

The developer runner `scripts/offline_path/runner.py` reuses the local bare-origin
and fake-GitHub approach from the preserved 2026-10-15 simulation. Historical
scripts and evidence are unchanged. The new runner observes current registered
CLI callbacks, not functions attributed to commands by a static ownership model.
It is not a public Kit command or a release driver for the real repository.

## Execution boundary

Use the repository's virtualenv Python and supply `--root` and a **new** `--out`
directory under the system temporary directory. macOS `sandbox-exec` is required;
there is no permissive fallback on other platforms. Existing output is refused.
The inherited OS policy denies network access and writes outside the owned root.
Before Kit execution, actual network and outside-write probes must return EPERM.
The runner uses a clean environment, local Git-only transport, an owned virtualenv,
read-only dependency paths, and an explicit `.pth` tracer import that also works
with Python `-I`. It does not install packages or use an external model.

The fixture is an archive of an exact Git source commit with synthetic one-commit
history, a local version tag and a neutral comment as the simulated product edit.
GitHub, PRs, merge actions and green `test` CI are local models. Successful fake CI
is an assumption, not a real CI observation. Unknown API endpoints return an error.
No tag, release, PR or file in the real project is changed by the experiment.
The sandbox is an execution/write boundary, not a confidentiality sandbox: source
and dependency reads are allowed. Raw local output must be reviewed before export.

Each step records its rc, structured verdict, time, stdout and stderr separately.
A zero rc with BLOCKED, FAIL or missing required JSON is not success. Unexpected
results stop, retain all evidence and return rc 3 / INCOMPLETE. A bounded completed
scenario returns 0 / BOUNDED_COMPLETE; this does not mean a live release passed.
The overall bound is 45 minutes and each step is limited to 15 minutes. Timed-out
process groups are killed; evidence is not automatically repaired or deleted.

## What a trace means

Each event records a callback entry, its unique call ID and its immediate parent.
Subprocesses inherit the active callback ancestry. A wrapper assembling argv with
`*parts` does not hide an executed callback. Direct edges and transitive ancestry
are separate; entering a callback does not prove successful completion. Shared
callback aliases are retained and matched to actual argv; unresolved identity is
reported as ambiguous, never assigned a guessed command. A missing event is not
proof that a path cannot execute. Threads, direct API calls, unexercised branches,
external executors and arbitrary internal function semantics are outside coverage.
The observation is pinned to a source commit and runner file hashes.

## Website figures

G2 is an editorial work sequence. Its commands, help and metadata come from the
current command manifest and the human workflow guide. It shows when to inspect,
change, check, finish and hand off; its arrows are not a runtime call graph.
G3 projects the current successor package filenames from the handoff generator;
a package-shape change blocks rendering until reviewed. Validation and source
inspection remain required before a successor continues.

G0 uses only direct observed callback edges for selected work/handoff/release
entrypoints. The exact source commit, incomplete status and stopped steps remain
visible. A blocked release prefix does not become a complete release path.
`understand/workflow-figures.json` contains public source bindings and the full
observed edge list. SVGs and visible HTML text alternatives are generated together;
no bitmap generation service or hand-maintained architecture taxonomy is used.
Orchestrators, primitives/diagnostics and shared protection mechanisms stay
separate. No universal lock, kernel, Microkernel or complete coverage is claimed.

## Regression and reproduction

`tests/test_offline_path_observation.py` checks wrapper/subprocess tracing,
Python-isolated tracer loading, alias inventory, direct edges, conservative
verdicts and OS policy construction. The actual OS probe is run before every
experiment, not silently skipped in a cross-platform unit test.
`tests/test_site_workflow_figures.py` checks deterministic SVG/XML, visible text,
source-drift propagation, command/package refusal and public-field whitelisting.
The full experiment is an explicit developer action, never a side effect of the
unit suite or the site build. The evidence report records its actual stop point.
