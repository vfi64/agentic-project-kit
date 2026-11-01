# KIT-GF-094: release B activation preparation

Status: preparation on an unmerged PR branch. No release or version bump.

The one package-owned activation constant is True in the B branch. Release A
(1.1.11) retains False. No second switch, environment flag, dependency or CLI
route is introduced. The A tests explicitly select False, including isolated
probe processes; the shipped-default regression requires contract version 2.
The self-built A/B/A-prime wheel transition tests remain unchanged.

## Merge and release hold

The owner must explicitly confirm A adoption by all known external workspaces
before this PR can merge. That confirmation is PENDING. Main must retain False
until then. Keep the PR open, never partially merge it, and rebase the complete
branch if main advances. No private workspace identities are recorded here.

The owner reports A adoption and a passing v1 chat switch plus an installed
1.1.11 retest for an external desktop controller. This is context, not local
verification of B or proof that all known workspaces have adopted A.

GF-094 is CLOSED/unreleased for future KIT-GF-091 stamping at B. A's historical
PARTIAL exclusion is retained in a fixture. No fixed release version is assigned.
The existing local-return, consumer-rehearsal and owner-acceptance prerequisites
remain binding. KIT-GF-096 stays OPEN; its expiry is no later than the second
release after B, not after A.

## Verification

Local verification is IN_PROGRESS; see the adjacent JSON report. The intended
gates are the full suite, ruff, check, check-docs, doctor and machine contracts
094, 095, 097 and 098 from a fresh noneditable wheel. The transition fixture
builds its own distinct A/B/A-prime wheels and uses real installation and Git;
only PR observation and the explicitly simulated unsupported legacy preview
boundary are doubles.

After these gates pass, the independent consumer rehearsal must use published
PyPI 1.1.11 as its actual planner and a PR-built target wheel in a disposable
copy: A-to-B, B chat switch, content merge and post-merge-check without refresh,
B-to-A return, and direct 1.1.10-to-B completion. This rehearsal is NOT_RUN here;
owner acceptance is PENDING. Self-built local wheels do not replace that proof.

## Complexity balance

B activates existing modular rendering, byte comparison and runtime identity;
it adds no production module, third-party dependency, public command or generic
workflow framework. The only additional production behavior beyond activation
is a more precise advisory for installed versions below 1.1.11. Tests preserve
the independent A path and B default. Existing typed results and evidence are
sufficient; an additional DCO cell layer would add complexity here.

The existing retest adapter also needs two bounded fixture corrections under
the B default: skip an empty migration commit when init already produced the
same v2 bytes, and remove the caller's PYTHONPATH before checking the owned
returned A-prime runtime. Existing 084/094 and 097/098 contracts reproduced the
failures. Their expectations and the real wheel-transition code remain unchanged.
The adapter's existing mixed fixture-dispatch responsibilities remain; no new
framework or broader runner extraction is introduced in this activation slice.

For external workspaces, an unchanged captured-input set after a content merge
no longer needs a refresh-only PR. Chat switches leave the versioned handoff
files byte-identical: changing HEAD, branch, time and run identity belongs to
the ignored runtime record, so it produces no tracked handoff diff. Physical
runtime evidence is preserved, not deleted. Changed authority inputs still
require governed regeneration. Self-hosting keeps its existing C4 lifecycle.
Legacy v1 compatibility is retained until KIT-GF-096; it is not removed now.
No measured CI/runtime saving or productive consumer verification is claimed.
