# KIT-GF-099: target-preview repository identity survives Git quoting

Consumer: an external desktop controller. Fix only; no version bump or release.

## Cause and correction

Published A (1.1.11) sends a quoted origin string to the target preview. The old
target parser retained the quotes and could not resolve the GitHub repository;
preview fell back to project_name. Actual target check read the unquoted real
origin, so repository_name and execution_contract changed after installation.
Fixing only future planners would not fix that released A caller.

The target parser now decodes complete Git-quoted values and Git escapes,
retaining unquoted and incomplete values. Future preview writers use Git string
escaping rather than JSON escaping, preserving UTF-8 and special characters.
Both legacy 1.1.11 payloads and current output are tested against actual target
rendering and byte validation. No Git subprocess is added to the parser.

## Required old-parser counterprobe

Before either production correction, the new real-wheel fixture was executed
with the unchanged main parser. Its origin is the synthetic public-shaped
https://github.com/example/transition-fixture.git, while project_name is external.
Git insteadOf maps all fetch/push traffic to the disposable local bare origin.
No request is sent to that GitHub repository.

The counterprobe reproduced BLOCKED after install, ci_pins, entrypoints and
projection. Target check failed with projection_inputs_changed and exactly the
execution_contract/repository_name mismatch. No adoption receipt was written.
The adjacent JSON records the old parser SHA256 and sanitized actual result.
The fixture change therefore exposes the bug instead of merely checking the fix.

Local parser and preview regressions failed before the corrections. The preview
roundtrip compares repository_name and execution_contract input hashes, requires
the actual check to PASS, and compares every projected byte. A legacy-payload
case injects the exact JSON-quoted origin serialization used by 1.1.11.
The writer syntax tests also use Git itself to read quoted, escaped and UTF-8
values. Parser tests include an unmatched leading quote and an escaped final quote.

## Verification and boundaries

Full suite and fresh noneditable-wheel contracts 094, 095, 097, 098 and 099:
IN_PROGRESS. Contract 096 is not a machine contract. Source catalog is
CLOSED/unreleased; canonical exports are regenerated through the Kit.

The main activation constant stays False. Only this fix PR may merge after green
checks and must complete its post-merge handoff. No release is authorized.
After that, rebase the complete B PR, keep it draft and unmerged, and replace
PR-state wording in its guide and changelog with durable release semantics.
The independent published-PyPI-1.1.11 consumer rehearsal must then be repeated
without a probe patch; local synthetic A wheels do not replace it.

## Complexity balance

Two small symmetric Git string helpers remain in the cohesive identity module;
the preview writer reuses the encoder. No dependency, CLI route, new activation
switch, format migration or general Git configuration framework is added.
The existing real-wheel fixture gains identity/transport separation and exact
repository assertions. It retains real installers and Git; PR observation remains
a double. Structured existing evidence is sufficient; no additional DCO layer
is warranted. External v2 refresh reduction and self-hosting boundaries are unchanged.
