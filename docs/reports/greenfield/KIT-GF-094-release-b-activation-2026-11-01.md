# KIT-GF-094: release B activation preparation

## Current preparation, 2026-11-03

The owner accepted the documented consumer rehearsal and authorized steps 1–5:
verified A adoption by all known external workspaces, complete B rebase,
revalidation, merge and post-merge handoff. Release is reserved for the owner.
The full B suite passed (4,549 tests, 560 warnings, 1,035.35 seconds), the
seven real-wheel machine contracts passed, and the independent six-run
consumer rehearsal passed. The external A workspaces are verified on 1.1.11;
personal local changes in one workspace were restored byte-for-byte. Ruff,
`check`, `check-docs` and `doctor` passed. The companion JSON records these
results and the exact tested source revision. The original six B source/test
files remain byte-identical; GF-100 and GF-101 implementation/tests are
inherited unchanged from main. Merge and post-merge handoff remain to be done;
release is not authorized by this closeout.

## Historical preparation snapshot

The dated sections below preserve earlier evidence and hold states; they do
not override the current owner authorization or the companion JSON's results.

Status: preparation on an unmerged PR branch. No release or version bump.

The one package-owned activation constant is True in the B branch. Release A
(1.1.11) retains False. No second switch, environment flag, dependency or CLI
route is introduced. The A tests explicitly select False, including isolated
probe processes; the shipped-default regression requires contract version 2.
The self-built A/B/A-prime wheel transition tests remain unchanged.

## Merge and release hold

The owner confirmed adoption of A by all known external workspaces before this
PR can merge. This was verified against each workspace's owned Kit runtime and
the relevant post-merge state. No private workspace identities are recorded
here. Main retains False until the complete PR is merged.

The owner reports A adoption and a passing v1 chat switch plus an installed
1.1.11 retest for an external desktop controller. The separately verified
workspace adoption and B consumer rehearsal are recorded in the current
preparation snapshot above and the companion JSON.

GF-094 is CLOSED/unreleased for future KIT-GF-091 stamping at B. A's historical
PARTIAL exclusion is retained in a fixture. No fixed release version is assigned.
The existing local-return, consumer-rehearsal and owner-acceptance prerequisites
remain binding. KIT-GF-096 stays OPEN; its expiry is no later than the second
release after B, not after A.

## Verification

Historical local verification at implementation revision `54c507457ef25318076b574dbe18fcc696c0c904`:

| Check | Result |
|---|---|
| Full suite | 4513 passed, 560 warnings, 399.28 seconds |
| ruff / check / check-docs / doctor | PASS |
| Fresh noneditable wheel: 094 / 095 / 097 / 098 | Four PASS |
| Final release-stamp regression module | 7 passed |

The final stamp-test refinement allows a later genuine B version assignment
while excluding 1.1.11, so the preparation test does not block the actual future
release. It and the evidence report are checked separately after the full run;
production code is unchanged. Machine details and the local wheel hash are in
the adjacent JSON report. The transition fixture
builds its own distinct A/B/A-prime wheels and uses real installation and Git;
only PR observation and the explicitly simulated unsupported legacy preview
boundary are doubles.

That historical snapshot preceded the independent consumer rehearsal. The
current six-run real-wheel result is recorded below and in the companion JSON.

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

The repository version remains 1.1.11; no B release version is assigned. The
existing test-wheel builder can give the PR target a distinct disposable test
version. Its synthetic A wheel must not replace the published PyPI 1.1.11
planner in the independent rehearsal. Main and all published artifacts remain
unchanged; this activation stays on the unmerged PR branch.

## Rebase verification, 2026-11-02

After GF-099 #2724 and complete post-merge handoff #2725, all three B commits
were rebased onto daa14918. The implementation head acd77b9b passed the full
suite (4,526 tests, 560 warnings, 393.48 seconds), fresh installed-wheel
contracts 094/095/097/098/099 and all local gates. Original source/test changes
and main's GF-099 code are preserved byte-for-byte.

The [KIT-GF-100 rebase report](KIT-GF-100-rebase-detached-head-resolver-2026-11-02.md)
records exact Git continuation, all affected paths, the complete implementation
range-diff, total diff review and a separate isolated negative resolver probe.
100 is OPEN; its fix is not part of B. The guide and changelog now describe
release semantics; the current draft/merge/release hold stays in #2723.
Published-A consumer rehearsal and owner acceptance are still pending.

## Final B revalidation, 2026-11-03

The complete branch was rebased onto main `0681508bbfe771634d6822f6858af88cd7f4eb45`.
The requested range-diff (`6dde207e..6569fba5` against
`daa14918..b141df65`) and a focused B range-diff were reviewed. The original
three B implementation commits map to the rebased implementation commits;
the two later report-only commits are retained, and three mainline
GF-100/GF-101 handoff commits are newly present. The six original B source/test
files are unchanged, GF-100/GF-101 source and tests match main, and the total
pre-report-update diff against main is 20 files, 846 insertions and 46
deletions. The complete range-diff and patch are included in the following
appendix; the patch snapshot predates this final evidence-only report update.
Trailing whitespace in the embedded diff is rendered visibly as `␠` so the
report itself passes whitespace checks; remove that marker to recover the
original line ending.

The full suite passed: 4,549 passed, 560 warnings, 1,035.35 seconds. A freshly
installed noneditable 1.1.12 wheel reported PASS for KIT-GF-094, 095, 097, 098,
099, 100 and 101. The independent rehearsal used published 1.1.11 as planner,
an unpatched B wheel, and a published 1.1.10 legacy install; all six runs
passed, including the v1 return and direct legacy completion. The A workspaces
are on published 1.1.11. No release, tag, or merge has been performed.

## Rebase range-diff (requested comparison)

```diff
 -:  -------- >  1:  144a36a5 [codex] Resolve owned detached-rebase conflicts (GF-100) (#2726)
 -:  -------- >  2:  cc2104c6 Refresh handoff state after PR2726 (#2727)
 -:  -------- >  3:  e2fa971e [codex] Enable explicit missing CI injection (GF-101) (#2728)
 -:  -------- >  4:  0681508b Refresh handoff state after PR2728 (#2729)
 1:  7c009ee5 !  5:  51398421 Prepare external projection v2 activation for release B while preserving A evidence
    @@ .agentic/greenfield_findings.json
␠
      ## CHANGELOG.md ##
     @@
    - ## Unreleased
    + - Fixed: Resolve conflicted files during an owned detached-HEAD rebase while preserving branch and target guards (KIT-GF-100).
␠
    -+- Changed: Enable external handoff projection v2 for release B (KIT-GF-094). First adopt release A **1.1.11**, then B. This activation remains on the PR branch until the owner confirms that all known external workspaces have adopted A; no merge or release is authorized yet.
    + - Fixed: Preserve the repository identity in target handoff previews by decoding Git-quoted origin values in the target and writing Git syntax in future planners. Legacy 1.1.11 payloads remain compatible; real-wheel regressions now use a GitHub-shaped origin distinct from the project name (KIT-GF-099). No release or v2 activation is performed by this fix.
    ++- Changed: Enable external handoff projection v2 for release B (KIT-GF-094). First adopt release A **1.1.11**, then B. All known external workspaces must adopt A before B is released.
     +- Changed: External content merges with current captured inputs require no refresh-only PR. Chat switches keep versioned handoff projections byte-identical; volatile identity remains in the ignored runtime file, producing no tracked handoff diff. Self-hosting retains its existing lifecycle.
     +- Fixed: The release-check advisory covers installations below 1.1.11. A direct jump from **1.1.10 or older** to B requires the documented migration route followed by another `kit update`; missing original adoption evidence leaves no governed installation return. KIT-GF-096 must remove external v1 compatibility no later than the second release after B.
    -+
    +␠
      ## v1.1.11 - 2026-11-01
␠
    - - Fixed: Stage external projection v2 across two releases: A retains v1 behavior while shipping the future migration planner; only a separately approved B activates the package-owned switch (KIT-GF-097).
␠
      ## docs/DOCUMENTATION_COVERAGE.yaml ##
     @@ docs/DOCUMENTATION_COVERAGE.yaml: rules:
    @@ docs/DOCUMENTATION_COVERAGE.yaml: rules:
          terms:
          - KIT-GF-095
␠
    - ## docs/DOCUMENTATION_REGISTRY.yaml ##
    -@@ docs/DOCUMENTATION_REGISTRY.yaml: documents:
    -   - path: docs/reports/release/release-run-1.1.11.json
    -     class: evidence/log
    -     owner: maintainers
    -+  - path: docs/reports/greenfield/KIT-GF-094-release-b-activation-2026-11-01.md
    -+    class: evidence/log
    -+    owner: maintainers
    -+    status: active
    -+    summary: Release B activation preparation, all-workspace A adoption hold and complexity balance.
    -+  - path: docs/reports/greenfield/KIT-GF-094-release-b-activation-2026-11-01.json
    -+    class: evidence/log
    -+    owner: maintainers
    -+    status: active
    -+    summary: Local B evidence and unchanged pending consumer rehearsal and owner release prerequisites.
    -
      ## docs/TEST_GATES.md ##
    -@@
    +@@ docs/TEST_GATES.md: without changing conflict bytes or the index. Linked Git worktrees are covered.
␠
      ### External projection v2 and governed return
␠
    @@ docs/TEST_GATES.md
      individual argument limit through a temporary input file and checks its cleanup.
␠
␠
    - ## docs/governance/DOC_REGISTRY_SCOPE_DECISION.md ##
    -@@ docs/governance/DOC_REGISTRY_SCOPE_DECISION.md: Decision outcome: active registry scope is declared in `docs/DOC_REGISTRY_SCOPE.
    - | docs/planning/ | 2 | 2 | 0 |  |
    - | docs/reference/ | 11 | 11 | 0 |  |
    - | docs/releases/ | 1 | 1 | 0 |  |
    --| docs/reports/ | 244 | 78 | 166 |  |
    -+| docs/reports/ | 245 | 79 | 166 |  |
    - | docs/workflow/ | 12 | 12 | 0 |  |
    -␠
    - Notes:
    -
      ## docs/planning/PROJECT_DIRECTION.yaml ##
     @@ docs/planning/PROJECT_DIRECTION.yaml: meta:
                owner_approved: '2026-11-01'
    @@ docs/planning/PROJECT_DIRECTION.yaml: meta:
                  decision: F1
␠
      ## docs/reference/EXTERNAL_HANDOFF_V2.md ##
    -@@
    - # External successor handoff v2
    +@@ docs/reference/EXTERNAL_HANDOFF_V2.md: strings. A GitHub-shaped fixture origin is transported only to a disposable
    + local bare repository through Git insteadOf rewriting. This parsing fix does
    + not change the projection activation policy.
␠
    -+## Release B preparation and merge hold
    ++## Release B activation
     +
    -+This PR branch activates `EXTERNAL_PROJECTION_V2_ACTIVE = True`; its shipped
    -+default is projection contract 2. Main remains on release A (1.1.11) with the
    -+constant False until the owner explicitly confirms that **all known external
    -+workspaces have adopted A**. The B preparation PR stays open meanwhile. No
    -+partial merge, release, version bump or production migration is authorized.
    -+If main advances, rebase the complete PR before review.
    ++Release B activates `EXTERNAL_PROJECTION_V2_ACTIVE = True`; its shipped default
    ++is projection contract 2. Release A (1.1.11) retains the same single constant as
    ++False. There is no second switch or environment override.
     +
    -+After the local gates pass, the independent disposable consumer rehearsal uses
    -+published PyPI 1.1.11 as the actual planner and a wheel built from this PR as
    -+the target: A-to-B, B chat switch, a content merge with post-merge-check and no
    -+refresh PR, B-to-A return, and direct 1.1.10-to-B completion. Owner acceptance
    -+follows that rehearsal. The local self-built wheel matrix does not replace it.
    ++Before B is released, all known external workspaces must adopt A. The independent
    ++disposable consumer rehearsal uses published PyPI 1.1.11 as the actual planner
    ++and a B target wheel: A-to-B, B chat switch, a content merge with post-merge-check
    ++and no refresh PR, B-to-A return, and direct 1.1.10-to-B completion. Owner
    ++acceptance follows that rehearsal. Local self-built A wheels do not replace it.
     +
    -+GF-094 is CLOSED/unreleased in this branch so KIT-GF-091 can stamp it at the
    -+future B release, subject to the unchanged release prerequisites. Its release
    -+version is not guessed. The A fixture retains PARTIAL/unreleased and excludes
    -+094 from A stamping. KIT-GF-096 expires no later than the second release after B.
    ++KIT-GF-091 stamps GF-094 at release B after these prerequisites are satisfied;
    ++the fix version is not guessed. Release A retains PARTIAL/unreleased and
    ++excludes 094 from A stamping. KIT-GF-096 expires no later than the second release
    ++after B.
     +
      ## Two-release adoption (KIT-GF-097)
␠
    @@ docs/reference/EXTERNAL_HANDOFF_V2.md
      `external_projection_policy.py`. It ships the future target preview, adoption
      receipt, runtime-consumer and return capabilities while external generation and
      checks retain v1. It adds no `projection_contract_min` and does not report
    + `NEEDS_PROJECTION_MIGRATION` through its external workflows. Module presence is
    + never activation. There is no environment or workspace activation option.
    +␠
    +-Known external workspaces first adopt A. A later, separately approved release B
    +-changes that one constant to True. The installed A planner previews B, signs the
    ++Known external workspaces first adopt A (1.1.11). Release B changes that one
    ++constant to True. The installed A planner previews B, signs the
    + projection, manifest minimum and ignore-file changes, and writes adoption
    + evidence after successful execution. A-to-A-prime remains a v1 update.
    +␠
     @@ docs/reference/EXTERNAL_HANDOFF_V2.md: starts with B. B1 adoption additionally waits for recorded cycle 008.
␠
      ### Direct legacy-to-B completion and B release notes
    @@ docs/reference/EXTERNAL_HANDOFF_V2.md: starts with B. B1 adoption additionally w
␠
      If an old planner installs B before detecting missing migration, preserve its
      BLOCKED result and completed steps. Use the existing
    +@@ docs/reference/EXTERNAL_HANDOFF_V2.md: The local A/B/A-prime matrix uses real noneditable wheels, loopback package
    + resolution, owned runtimes and real bare-origin squashes. Only PR observation
    + is a test double. A direct jump simulates the unsupported preview boundary;
    + installation and completion remain real. Independent consumer rehearsal and
    +-owner acceptance remain release gates; no release is authorized here.
    ++owner acceptance remain release gates.
    +␠
    + When release B is active, KIT-GF-094 replaces commit freshness with deterministic content freshness only
    + for external workspaces. Self-hosting retains its v1 contract, C4 administrative
␠
      ## docs/reports/greenfield/EXTERNAL_FINDINGS_RETESTS.md ##
     @@ docs/reports/greenfield/EXTERNAL_FINDINGS_RETESTS.md: Expected result fields: `{"assertions": ["release_check.installed equals the run
    @@ docs/reports/greenfield/external-findings-status.json
      {
        "authority": "Kit adjudication; VERIFIED_FIXED belongs to the consuming workspace",
        "counts": {
    --    "CLOSED": 95,
    -+    "CLOSED": 96,
    +-    "CLOSED": 98,
    ++    "CLOSED": 99,
          "NOT_APPLICABLE": 0,
          "OPEN": 1,
     -    "PARTIAL": 1
    @@ docs/reports/greenfield/external-findings-status.json
            "external_retest": {
     @@
        "kind": "external_findings_status",
    -   "machine_contracts": 56,
    +   "machine_contracts": 59,
        "schema_version": 1,
    --  "source_sha256": "caa4b3f57ab770c30992ce93f99a9747c66723edac3ec2d6830db7a167e84a86"
    -+  "source_sha256": "40dd85fcd079c166c47f32082eb2ef431f1a55671b34827860abcf412475838b"
    +-  "source_sha256": "b564f951720c16cf7cab1b034a5d3f47127b5aef17ca8f839703f97169a143c9"
    ++  "source_sha256": "d661af7efb8724e30b896403fd38da6ebae422ddd4fd1c1569ebe0d4f45a6ee3"
      }
␠
      ## src/agentic_project_kit/external_projection_policy.py ##
    @@ src/agentic_project_kit/reference/external-findings-status.json
      {
        "authority": "Kit adjudication; VERIFIED_FIXED belongs to the consuming workspace",
        "counts": {
    --    "CLOSED": 95,
    -+    "CLOSED": 96,
    +-    "CLOSED": 98,
    ++    "CLOSED": 99,
          "NOT_APPLICABLE": 0,
          "OPEN": 1,
     -    "PARTIAL": 1
    @@ src/agentic_project_kit/reference/external-findings-status.json
            "external_retest": {
     @@
        "kind": "external_findings_status",
    -   "machine_contracts": 56,
    +   "machine_contracts": 59,
        "schema_version": 1,
    --  "source_sha256": "caa4b3f57ab770c30992ce93f99a9747c66723edac3ec2d6830db7a167e84a86"
    -+  "source_sha256": "40dd85fcd079c166c47f32082eb2ef431f1a55671b34827860abcf412475838b"
    +-  "source_sha256": "b564f951720c16cf7cab1b034a5d3f47127b5aef17ca8f839703f97169a143c9"
    ++  "source_sha256": "d661af7efb8724e30b896403fd38da6ebae422ddd4fd1c1569ebe0d4f45a6ee3"
      }
␠
      ## tests/test_external_projection_activation.py ##
 2:  54c50745 =  6:  3ffa64f1 Make B retest fixtures idempotent and isolate returned owned runtimes
 3:  6569fba5 =  7:  a960b83c Record B activation verification and preserve future release-stamp compatibility
 -:  -------- >  8:  334f35e4 Document B rebase preservation and open detached-HEAD resolver finding GF-100
 -:  -------- >  9:  7c295b10 Bind open GF-100 to a negative reproduction contract without changing the resolver
 -:  -------- > 10:  b141df65 Prepare complete B revalidation after GF-101 and owner acceptance

```

## Full diff against main (pre-report-update snapshot)

The following is the complete patch for the branch against main at the tested revision. It excludes this report amendment, which records the validation results and embeds the patch.

```diff
diff --git a/.agentic/greenfield_findings.json b/.agentic/greenfield_findings.json
index 9c5084e5..2eaf614c 100644
--- a/.agentic/greenfield_findings.json
+++ b/.agentic/greenfield_findings.json
@@ -6975,10 +6975,10 @@
     },
     {
       "id": "KIT-GF-094",
-      "kit_state": "PARTIAL",
+      "kit_state": "CLOSED",
       "fixed_in": "unreleased",
       "prs": [],
-      "report": "docs/reports/greenfield/KIT-GF-094-external-handoff-v2-2026-11-01.md",
+      "report": "docs/reports/greenfield/KIT-GF-094-release-b-activation-2026-11-01.md",
       "external_retest": {
         "workspace_kind": "external_manifest",
         "preconditions": [
@@ -7296,7 +7296,7 @@
             }
           ]
         },
-        "verification": "Implementation retained behind the package activation constant. Release A remains v1; GF-094 becomes effective only in separately approved release B. Consumer rehearsal and owner acceptance remain required."
+        "verification": "This local machine contract is not consumer acceptance. Independent published-PyPI-A rehearsal, local return and owner acceptance are recorded in the linked release-prerequisite report; consumer VERIFIED_FIXED remains independent."
       }
     },
     {
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 9c4c18d3..822ec83d 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -5,6 +5,9 @@
 - Fixed: Resolve conflicted files during an owned detached-HEAD rebase while preserving branch and target guards (KIT-GF-100).
␠
 - Fixed: Preserve the repository identity in target handoff previews by decoding Git-quoted origin values in the target and writing Git syntax in future planners. Legacy 1.1.11 payloads remain compatible; real-wheel regressions now use a GitHub-shaped origin distinct from the project name (KIT-GF-099). No release or v2 activation is performed by this fix.
+- Changed: Enable external handoff projection v2 for release B (KIT-GF-094). First adopt release A **1.1.11**, then B. All known external workspaces must adopt A before B is released.
+- Changed: External content merges with current captured inputs require no refresh-only PR. Chat switches keep versioned handoff projections byte-identical; volatile identity remains in the ignored runtime file, producing no tracked handoff diff. Self-hosting retains its existing lifecycle.
+- Fixed: The release-check advisory covers installations below 1.1.11. A direct jump from **1.1.10 or older** to B requires the documented migration route followed by another `kit update`; missing original adoption evidence leaves no governed installation return. KIT-GF-096 must remove external v1 compatibility no later than the second release after B.
␠
 ## v1.1.11 - 2026-11-01
␠
diff --git a/docs/DOCUMENTATION_COVERAGE.yaml b/docs/DOCUMENTATION_COVERAGE.yaml
index 49c2bed7..c16617ef 100644
--- a/docs/DOCUMENTATION_COVERAGE.yaml
+++ b/docs/DOCUMENTATION_COVERAGE.yaml
@@ -50,6 +50,8 @@ rules:
     - EXTERNAL_PROJECTION_V2_ACTIVE
     - release A
     - release B
+    - all known external
+    - PyPI 1.1.11
   - path: docs/KIT_UPDATE_RETURN.md
     terms:
     - KIT-GF-095
diff --git a/docs/DOCUMENTATION_REGISTRY.yaml b/docs/DOCUMENTATION_REGISTRY.yaml
index 52463c16..37cd5ceb 100644
--- a/docs/DOCUMENTATION_REGISTRY.yaml
+++ b/docs/DOCUMENTATION_REGISTRY.yaml
@@ -2000,3 +2000,19 @@ documents:
     status: active
     summary: Explicit managed CI injection for initialized external workspaces; regression
       and gate evidence.
+  - path: docs/reports/greenfield/KIT-GF-094-release-b-activation-2026-11-01.md
+    class: evidence/log
+    owner: maintainers
+    status: active
+    summary: Release B activation, rebased verification and consumer acceptance evidence.
+  - path: docs/reports/greenfield/KIT-GF-094-release-b-activation-2026-11-01.json
+    class: evidence/log
+    owner: maintainers
+    status: active
+    summary: Machine-readable B activation and release prerequisites.
+  - path: docs/reports/greenfield/KIT-GF-100-rebase-detached-head-resolver-2026-11-02.json
+    class: evidence/log
+    owner: maintainers
+    status: active
+    summary: Historical pre-fix detached-rebase failure evidence; superseded by the GF-100
+      fix.
diff --git a/docs/TEST_GATES.md b/docs/TEST_GATES.md
index c8f050f2..21d2f048 100644
--- a/docs/TEST_GATES.md
+++ b/docs/TEST_GATES.md
@@ -15,15 +15,19 @@ without changing conflict bytes or the index. Linked Git worktrees are covered.
␠
 ### External projection v2 and governed return
␠
-`tests/test_external_projection_activation.py` checks the release A default and
-single activation boundary. Historical v2 contracts explicitly activate B.
+`tests/test_external_projection_activation.py` checks the shipped release B
+default (contract 2), the explicit False release A fixtures and the single
+activation boundary. Isolated A probe processes also explicitly patch False;
+there is no production environment override. Historical v2 contracts activate B.
 `tests/test_projection_release_wheels.py` verifies A/B/A-prime wheel identities.
 `tests/test_projection_release_transition.py` installs them through a loopback
 index: installed A plans B, real squashes retain content freshness, governed
 return restores A, A-to-A-prime stays v1, and a legacy unsupported-preview attempt
 completes through existing routes. Only PR observation is doubled. Fresh
-noneditable-wheel retests are required for KIT-GF-097 and KIT-GF-098. Release A
-does not stamp PARTIAL KIT-GF-094 as fixed.
+noneditable-wheel retests are required for KIT-GF-097 and KIT-GF-098.
+`tests/test_release_greenfield_stamp.py` retains A's PARTIAL exclusion fixture
+and requires B's CLOSED/unreleased catalog, without weakening the consumer
+rehearsal and owner acceptance gates. KIT-GF-096 expires from B, not A.
 The target-preview regression also transfers inputs larger than Linux's
 individual argument limit through a temporary input file and checks its cleanup.
␠
diff --git a/docs/governance/DOC_REGISTRY_SCOPE_DECISION.md b/docs/governance/DOC_REGISTRY_SCOPE_DECISION.md
index 36c1c319..9bfca237 100644
--- a/docs/governance/DOC_REGISTRY_SCOPE_DECISION.md
+++ b/docs/governance/DOC_REGISTRY_SCOPE_DECISION.md
@@ -24,7 +24,7 @@ Decision outcome: active registry scope is declared in `docs/DOC_REGISTRY_SCOPE.
 | docs/planning/ | 2 | 2 | 0 |  |
 | docs/reference/ | 11 | 11 | 0 |  |
 | docs/releases/ | 1 | 1 | 0 |  |
-| docs/reports/ | 247 | 81 | 166 |  |
+| docs/reports/ | 248 | 82 | 166 |  |
 | docs/workflow/ | 12 | 12 | 0 |  |
␠
 Notes:
diff --git a/docs/planning/PROJECT_DIRECTION.yaml b/docs/planning/PROJECT_DIRECTION.yaml
index f4e6416c..461a807c 100644
--- a/docs/planning/PROJECT_DIRECTION.yaml
+++ b/docs/planning/PROJECT_DIRECTION.yaml
@@ -117,10 +117,10 @@ meta:
           owner_approved: '2026-11-01'
           scope: Two-release external projection transition; A retains v1, then known external workspaces adopt A, then separately approved B activates v2.
           two_release_transition:
-          - Release A ships target preview, adoption evidence, return and runtime-consumer capabilities with the package activation constant False.
-          - Record release A adoption in every known external workspace before proposing release B.
-          - Release B is a later owner-approved small PR changing the constant to True; GF-094 becomes effective and GF-096 expiry starts then.
-          - B1 adopts B only after cycle 008 is completed and recorded.
+          - Released A (1.1.11) ships target preview, adoption evidence, return and runtime-consumer capabilities with the package activation constant False.
+          - Prepare B on an open PR branch; keep main False until the owner explicitly confirms release A adoption in every known external workspace.
+          - B changes the single constant to True; no partial merge or publication before the adoption confirmation, independent consumer rehearsal and owner acceptance. Rebase the whole PR if main advances.
+          - KIT-GF-094 stays unreleased until B stamping; KIT-GF-096 expires no later than the second release after B. A remaining known workspace adopts A after its current cycle.
           supersedes_for_external_mode:
             source: docs/reports/POST_0_5_0_C4_REFRESH_CHAIN_DECISION_20260813.md
             decision: F1
diff --git a/docs/reference/EXTERNAL_HANDOFF_V2.md b/docs/reference/EXTERNAL_HANDOFF_V2.md
index 4565c441..24fc1acd 100644
--- a/docs/reference/EXTERNAL_HANDOFF_V2.md
+++ b/docs/reference/EXTERNAL_HANDOFF_V2.md
@@ -7,17 +7,34 @@ strings. A GitHub-shaped fixture origin is transported only to a disposable
 local bare repository through Git insteadOf rewriting. This parsing fix does
 not change the projection activation policy.
␠
+## Release B activation
+
+Release B activates `EXTERNAL_PROJECTION_V2_ACTIVE = True`; its shipped default
+is projection contract 2. Release A (1.1.11) retains the same single constant as
+False. There is no second switch or environment override.
+
+Before B is released, all known external workspaces must adopt A. The independent
+disposable consumer rehearsal uses published PyPI 1.1.11 as the actual planner
+and a B target wheel: A-to-B, B chat switch, a content merge with post-merge-check
+and no refresh PR, B-to-A return, and direct 1.1.10-to-B completion. Owner
+acceptance follows that rehearsal. Local self-built A wheels do not replace it.
+
+KIT-GF-091 stamps GF-094 at release B after these prerequisites are satisfied;
+the fix version is not guessed. Release A retains PARTIAL/unreleased and
+excludes 094 from A stamping. KIT-GF-096 expires no later than the second release
+after B.
+
 ## Two-release adoption (KIT-GF-097)
␠
-Release A is the expand release: `EXTERNAL_PROJECTION_V2_ACTIVE = False` in
+Release A (1.1.11) is the expand release: `EXTERNAL_PROJECTION_V2_ACTIVE = False` in
 `external_projection_policy.py`. It ships the future target preview, adoption
 receipt, runtime-consumer and return capabilities while external generation and
 checks retain v1. It adds no `projection_contract_min` and does not report
 `NEEDS_PROJECTION_MIGRATION` through its external workflows. Module presence is
 never activation. There is no environment or workspace activation option.
␠
-Known external workspaces first adopt A. A later, separately approved release B
-changes that one constant to True. The installed A planner previews B, signs the
+Known external workspaces first adopt A (1.1.11). Release B changes that one
+constant to True. The installed A planner previews B, signs the
 projection, manifest minimum and ignore-file changes, and writes adoption
 evidence after successful execution. A-to-A-prime remains a v1 update.
␠
@@ -27,10 +44,10 @@ starts with B. B1 adoption additionally waits for recorded cycle 008.
␠
 ### Direct legacy-to-B completion and B release notes
␠
-The required B release-note guidance is: **Install release A before B**,
+The required B release-note guidance is: **Install release A (1.1.11) before B**,
 so A can plan the first migration and record evidence for return to A.
 The optional `kit status --check-release` notice explains this sequence for
-legacy installations when an update beyond 1.1.10 is available.
+installations below 1.1.11 when release A or a newer release is available.
␠
 If an old planner installs B before detecting missing migration, preserve its
 BLOCKED result and completed steps. Use the existing
@@ -44,7 +61,7 @@ The local A/B/A-prime matrix uses real noneditable wheels, loopback package
 resolution, owned runtimes and real bare-origin squashes. Only PR observation
 is a test double. A direct jump simulates the unsupported preview boundary;
 installation and completion remain real. Independent consumer rehearsal and
-owner acceptance remain release gates; no release is authorized here.
+owner acceptance remain release gates.
␠
 When release B is active, KIT-GF-094 replaces commit freshness with deterministic content freshness only
 for external workspaces. Self-hosting retains its v1 contract, C4 administrative
diff --git a/docs/reports/greenfield/EXTERNAL_FINDINGS_RETESTS.md b/docs/reports/greenfield/EXTERNAL_FINDINGS_RETESTS.md
index b5b7384b..be86ce66 100644
--- a/docs/reports/greenfield/EXTERNAL_FINDINGS_RETESTS.md
+++ b/docs/reports/greenfield/EXTERNAL_FINDINGS_RETESTS.md
@@ -1592,8 +1592,8 @@ Expected result fields: `{"assertions": ["release_check.installed equals the run
␠
 ## KIT-GF-094
␠
-Kit state: PARTIAL; fixed_in: unreleased.
-Evidence: docs/reports/greenfield/KIT-GF-094-external-handoff-v2-2026-11-01.md
+Kit state: CLOSED; fixed_in: unreleased.
+Evidence: docs/reports/greenfield/KIT-GF-094-release-b-activation-2026-11-01.md
␠
 Execution class: local (effects: none); machine contract: Real local bare-origin squash, stale input rejection, regeneration, exact runtime HEAD, unique runs and unchanged durable bytes.
␠
diff --git a/docs/reports/greenfield/KIT-GF-094-release-b-activation-2026-11-01.json b/docs/reports/greenfield/KIT-GF-094-release-b-activation-2026-11-01.json
new file mode 100644
index 00000000..ba379a57
--- /dev/null
+++ b/docs/reports/greenfield/KIT-GF-094-release-b-activation-2026-11-01.json
@@ -0,0 +1,515 @@
+{
+  "schema_version": 1,
+  "finding": "KIT-GF-094",
+  "fixed_in": "unreleased",
+  "implementation_status": "IMPLEMENTED_LOCALLY_VERIFIED",
+  "consumer": "an external desktop controller",
+  "base_commit": "6dde207eb96cbd9a0cee0a75113070fd4b836b75",
+  "release_A": "1.1.11",
+  "activation": true,
+  "merge_hold": "PENDING_ALL_KNOWN_WORKSPACES_ON_A",
+  "consumer_evidence": "Prior full independent published-A rehearsal PASS; complete repeat on the GF-101-rebased B target pending before merge.",
+  "release_prerequisites": {
+    "local_return": "PASS",
+    "consumer_rehearsal": "NOT_RUN",
+    "owner_acceptance": "PASS"
+  },
+  "machine_contracts": {
+    "KIT-GF-094": "PASS",
+    "KIT-GF-095": "PASS",
+    "KIT-GF-097": "PASS",
+    "KIT-GF-098": "PASS"
+  },
+  "full_suite": {
+    "status": "PASS",
+    "command": "python -m pytest -q -n 4",
+    "passed": 4513,
+    "warnings": 560,
+    "seconds": 399.28,
+    "source_revision": "54c507457ef25318076b574dbe18fcc696c0c904"
+  },
+  "gates": {
+    "check": {
+      "command": "agentic-kit check --json",
+      "status": "PASS"
+    },
+    "check_docs": {
+      "command": "agentic-kit check-docs",
+      "status": "PASS"
+    },
+    "ruff": {
+      "command": "ruff check .",
+      "status": "PASS"
+    },
+    "doctor": {
+      "command": "agentic-kit doctor",
+      "status": "PASS"
+    }
+  },
+  "complexity": {
+    "new_production_modules": 0,
+    "new_dependencies": 0,
+    "new_public_commands": 0,
+    "external_refresh_pr_after_current_input_content_merge": false,
+    "tracked_handoff_changes_after_chat_switch": false,
+    "ignored_runtime_evidence_retained": true,
+    "selfhosting_changed": false
+  },
+  "expiry": "KIT-GF-096: no later than the second release after B",
+  "release_performed": false,
+  "merge_performed": false,
+  "implementation_revision": "54c507457ef25318076b574dbe18fcc696c0c904",
+  "final_release_stamp_tests": {
+    "status": "PASS",
+    "passed": 7,
+    "command": "python -m pytest -q tests/test_release_greenfield_stamp.py",
+    "scope": "A exclusion, B eligibility, pending prerequisites and future real B stamp compatibility"
+  },
+  "machine": {
+    "result_status": "PASS",
+    "counts": {
+      "FAIL": 0,
+      "NOT_RUN_LOCALLY": 0,
+      "NO_MACHINE_CONTRACT": 0,
+      "PASS": 4
+    },
+    "executed_from": "fresh_noneditable_installed_wheel",
+    "source_revision": "54c507457ef25318076b574dbe18fcc696c0c904",
+    "records": [
+      {
+        "covers": "Real local bare-origin squash, stale input rejection, regeneration, exact runtime HEAD, unique runs and unchanged durable bytes.",
+        "execution_class": "local",
+        "failures": [],
+        "fixed_in": "unreleased",
+        "id": "KIT-GF-094",
+        "kit_state": "CLOSED",
+        "remote_effects": [
+          "none"
+        ],
+        "result": "PASS",
+        "steps": [
+          {
+            "argv": [
+              "git",
+              "switch",
+              "-c",
+              "product"
+            ],
+            "failures": [],
+            "index": 0,
+            "returncode": 0
+          },
+          {
+            "failures": [],
+            "index": 1,
+            "write": "product.txt"
+          },
+          {
+            "argv": [
+              "git",
+              "add",
+              "product.txt"
+            ],
+            "failures": [],
+            "index": 2,
+            "returncode": 0
+          },
+          {
+            "argv": [
+              "git",
+              "commit",
+              "-m",
+              "Product work without handoff inputs"
+            ],
+            "failures": [],
+            "index": 3,
+            "returncode": 0
+          },
+          {
+            "argv": [
+              "git",
+              "switch",
+              "main"
+            ],
+            "failures": [],
+            "index": 4,
+            "returncode": 0
+          },
+          {
+            "argv": [
+              "git",
+              "merge",
+              "--squash",
+              "product"
+            ],
+            "failures": [],
+            "index": 5,
+            "returncode": 0
+          },
+          {
+            "argv": [
+              "git",
+              "commit",
+              "-m",
+              "Squash product"
+            ],
+            "failures": [],
+            "index": 6,
+            "returncode": 0
+          },
+          {
+            "argv": [
+              "git",
+              "push",
+              "origin",
+              "main"
+            ],
+            "failures": [],
+            "index": 7,
+            "returncode": 0
+          },
+          {
+            "argv": [
+              "agentic-kit",
+              "transfer",
+              "post-merge-check"
+            ],
+            "failures": [],
+            "index": 8,
+            "returncode": 0
+          },
+          {
+            "argv": [
+              "git",
+              "switch",
+              "-c",
+              "authority"
+            ],
+            "failures": [],
+            "index": 9,
+            "returncode": 0
+          },
+          {
+            "failures": [],
+            "index": 10,
+            "write": ".agentic/state/status.md"
+          },
+          {
+            "argv": [
+              "agentic-kit",
+              "check"
+            ],
+            "failures": [],
+            "index": 11,
+            "returncode": 1
+          },
+          {
+            "argv": [
+              "agentic-kit",
+              "transfer",
+              "chat-switch-complete",
+              "--json"
+            ],
+            "failures": [],
+            "index": 12,
+            "returncode": 0
+          },
+          {
+            "argv": [
+              "git",
+              "add",
+              "-A"
+            ],
+            "failures": [],
+            "index": 13,
+            "returncode": 0
+          },
+          {
+            "argv": [
+              "git",
+              "commit",
+              "-m",
+              "Update authority with deterministic projection"
+            ],
+            "failures": [],
+            "index": 14,
+            "returncode": 0
+          },
+          {
+            "argv": [
+              "git",
+              "switch",
+              "main"
+            ],
+            "failures": [],
+            "index": 15,
+            "returncode": 0
+          },
+          {
+            "argv": [
+              "git",
+              "merge",
+              "--squash",
+              "authority"
+            ],
+            "failures": [],
+            "index": 16,
+            "returncode": 0
+          },
+          {
+            "argv": [
+              "git",
+              "commit",
+              "-m",
+              "Squash authority"
+            ],
+            "failures": [],
+            "index": 17,
+            "returncode": 0
+          },
+          {
+            "argv": [
+              "git",
+              "push",
+              "origin",
+              "main"
+            ],
+            "failures": [],
+            "index": 18,
+            "returncode": 0
+          },
+          {
+            "argv": [
+              "agentic-kit",
+              "transfer",
+              "post-merge-check"
+            ],
+            "failures": [],
+            "index": 19,
+            "returncode": 0
+          },
+          {
+            "argv": [
+              "agentic-kit",
+              "transfer",
+              "chat-switch-complete",
+              "--json"
+            ],
+            "failures": [],
+            "index": 20,
+            "returncode": 0
+          },
+          {
+            "argv": [
+              "git",
+              "rev-parse",
+              "HEAD"
+            ],
+            "failures": [],
+            "index": 21,
+            "returncode": 0
+          },
+          {
+            "failures": [],
+            "index": 22,
+            "write": ".agentic/tmp/first-run"
+          },
+          {
+            "argv": [
+              "agentic-kit",
+              "transfer",
+              "chat-switch-complete",
+              "--json"
+            ],
+            "failures": [],
+            "index": 23,
+            "returncode": 0
+          },
+          {
+            "failures": [],
+            "index": 24,
+            "write": ".agentic/tmp/second-run"
+          },
+          {
+            "argv": [
+              "git",
+              "diff",
+              "--no-index",
+              ".agentic/tmp/first-run",
+              ".agentic/tmp/second-run"
+            ],
+            "failures": [],
+            "index": 25,
+            "returncode": 1
+          },
+          {
+            "argv": [
+              "git",
+              "diff",
+              "--exit-code"
+            ],
+            "failures": [],
+            "index": 26,
+            "returncode": 0
+          }
+        ]
+      },
+      {
+        "covers": "Real local Git adoption and return squashes, byte-exact v1 restoration including ignored runtime backup, later-touch no-mutation, wrong state/version rejection; existing update executor with installation double and real fresh-process snapshot checks.",
+        "execution_class": "local",
+        "failures": [],
+        "fixed_in": "1.1.11",
+        "id": "KIT-GF-095",
+        "kit_state": "CLOSED",
+        "remote_effects": [
+          "none"
+        ],
+        "result": "PASS",
+        "steps": [
+          {
+            "argv": [
+              "agentic-kit",
+              "check",
+              "--json"
+            ],
+            "failures": [],
+            "index": 0,
+            "returncode": 1
+          },
+          {
+            "argv": [
+              "git",
+              "diff",
+              "--no-index",
+              ".agentic/tmp/return-contract/expected.json",
+              ".agentic/tmp/return-contract/actual.json"
+            ],
+            "failures": [],
+            "index": 1,
+            "returncode": 0
+          }
+        ]
+      },
+      {
+        "covers": "Installed predecessor plans the first active projection migration using real noneditable A/B/A-prime wheels, actual pip installation, local origin and squashes.",
+        "execution_class": "local",
+        "failures": [],
+        "fixed_in": "1.1.11",
+        "id": "KIT-GF-097",
+        "kit_state": "CLOSED",
+        "remote_effects": [
+          "none"
+        ],
+        "result": "PASS",
+        "steps": [
+          {
+            "assert": {
+              "exists": [
+                ".agentic/tmp/transition-proof.json"
+              ]
+            },
+            "failures": [],
+            "index": 0
+          },
+          {
+            "argv": [
+              "agentic-kit",
+              "check",
+              "--json"
+            ],
+            "failures": [],
+            "index": 1,
+            "returncode": 0
+          }
+        ]
+      },
+      {
+        "covers": "Return targets the exact previous pinned Kit version using real noneditable A/B/A-prime wheels, actual pip installation, local origin and squashes.",
+        "execution_class": "local",
+        "failures": [],
+        "fixed_in": "1.1.11",
+        "id": "KIT-GF-098",
+        "kit_state": "CLOSED",
+        "remote_effects": [
+          "none"
+        ],
+        "result": "PASS",
+        "steps": [
+          {
+            "assert": {
+              "exists": [
+                ".agentic/tmp/transition-proof.json"
+              ]
+            },
+            "failures": [],
+            "index": 0
+          },
+          {
+            "argv": [
+              "agentic-kit",
+              "check",
+              "--json"
+            ],
+            "failures": [],
+            "index": 1,
+            "returncode": 0
+          }
+        ]
+      }
+    ]
+  },
+  "wheel": {
+    "filename": "agentic_project_kit-1.1.11-py3-none-any.whl",
+    "sha256": "98e21b343286951cc6e5899cc2650283ea270e8708eb2daa21f9addcf7bf6ea8",
+    "kind": "local_unreleased_B_branch_test_build",
+    "published": false
+  },
+  "fixture_versions": {
+    "A": "1.1.11",
+    "B": "1.1.12",
+    "A_prime": "1.1.11.post1",
+    "kind": "synthetic_test_versions"
+  },
+  "fixture_corrections": [
+    "Skip a no-op v2 migration commit after B init.",
+    "Remove the extracted caller PYTHONPATH before the final owned A-prime check."
+  ],
+  "rebase_validation": {
+    "date": "2026-11-02",
+    "base_commit": "daa149180937f03982187824b54f0d4acd11d999",
+    "source_revision": "acd77b9b2a2a01d1c2338dca7569996058ba3354",
+    "full_suite": {
+      "status": "PASS",
+      "passed": 4526,
+      "warnings": 560,
+      "seconds": 393.48
+    },
+    "machine_contracts": {
+      "KIT-GF-094": "PASS",
+      "KIT-GF-095": "PASS",
+      "KIT-GF-097": "PASS",
+      "KIT-GF-098": "PASS",
+      "KIT-GF-099": "PASS"
+    },
+    "six_original_B_source_and_test_files_unchanged": true,
+    "GF_099_inherited_unchanged": true,
+    "finding": "KIT-GF-100",
+    "finding_status": "OPEN",
+    "resolver_fix_included": false,
+    "report": "docs/reports/greenfield/KIT-GF-100-rebase-detached-head-resolver-2026-11-02.md",
+    "merge_performed": false,
+    "release_performed": false,
+    "finding_negative_reproduction_contract": "PASS; 19 steps, OPEN remains"
+  },
+  "final_preparation": {
+    "date": "2026-11-03",
+    "main_base": "0681508bbfe771634d6822f6858af88cd7f4eb45",
+    "B_original_six_files_byte_identical": true,
+    "GF100_GF101_source_and_tests_match_main": true,
+    "owner_authorized_steps": "1 through 5, including conditional merge and handoff; no release",
+    "owner_acceptance_source": "Owner chat: Owner-Abnahme B auf Grundlage der dokumentierten Verbraucherprobe erteilt.",
+    "full_suite": "PENDING",
+    "independent_rehearsal": "PENDING",
+    "all_known_external_workspaces_A": "PENDING_REMOTE_CLOSEOUT"
+  }
+}
diff --git a/docs/reports/greenfield/KIT-GF-094-release-b-activation-2026-11-01.md b/docs/reports/greenfield/KIT-GF-094-release-b-activation-2026-11-01.md
new file mode 100644
index 00000000..93f2ff4a
--- /dev/null
+++ b/docs/reports/greenfield/KIT-GF-094-release-b-activation-2026-11-01.md
@@ -0,0 +1,115 @@
+# KIT-GF-094: release B activation preparation
+
+## Current preparation, 2026-11-03
+
+The owner accepted the documented consumer rehearsal and authorized steps 1–5:
+verified A adoption by all known external workspaces, complete B rebase,
+revalidation, merge and post-merge handoff. Release is reserved for the owner.
+The companion JSON's `final_preparation` and `release_prerequisites` fields
+record the current verified state. Pending checks are never treated as PASS.
+The complete original six B source/test files remain byte-identical; GF-100
+and GF-101 code/tests are inherited unchanged from main. The isolated external
+A adoption and complete real-wheel consumer matrix are verified separately.
+
+## Historical preparation snapshot
+
+The dated sections below preserve earlier evidence and hold states; they do
+not override the current owner authorization or the companion JSON's results.
+
+Status: preparation on an unmerged PR branch. No release or version bump.
+
+The one package-owned activation constant is True in the B branch. Release A
+(1.1.11) retains False. No second switch, environment flag, dependency or CLI
+route is introduced. The A tests explicitly select False, including isolated
+probe processes; the shipped-default regression requires contract version 2.
+The self-built A/B/A-prime wheel transition tests remain unchanged.
+
+## Merge and release hold
+
+The owner must explicitly confirm A adoption by all known external workspaces
+before this PR can merge. That confirmation is PENDING. Main must retain False
+until then. Keep the PR open, never partially merge it, and rebase the complete
+branch if main advances. No private workspace identities are recorded here.
+
+The owner reports A adoption and a passing v1 chat switch plus an installed
+1.1.11 retest for an external desktop controller. This is context, not local
+verification of B or proof that all known workspaces have adopted A.
+
+GF-094 is CLOSED/unreleased for future KIT-GF-091 stamping at B. A's historical
+PARTIAL exclusion is retained in a fixture. No fixed release version is assigned.
+The existing local-return, consumer-rehearsal and owner-acceptance prerequisites
+remain binding. KIT-GF-096 stays OPEN; its expiry is no later than the second
+release after B, not after A.
+
+## Verification
+
+Local verification at implementation revision `54c507457ef25318076b574dbe18fcc696c0c904`:
+
+| Check | Result |
+|---|---|
+| Full suite | 4513 passed, 560 warnings, 399.28 seconds |
+| ruff / check / check-docs / doctor | PASS |
+| Fresh noneditable wheel: 094 / 095 / 097 / 098 | Four PASS |
+| Final release-stamp regression module | 7 passed |
+
+The final stamp-test refinement allows a later genuine B version assignment
+while excluding 1.1.11, so the preparation test does not block the actual future
+release. It and the evidence report are checked separately after the full run;
+production code is unchanged. Machine details and the local wheel hash are in
+the adjacent JSON report. The transition fixture
+builds its own distinct A/B/A-prime wheels and uses real installation and Git;
+only PR observation and the explicitly simulated unsupported legacy preview
+boundary are doubles.
+
+The independent consumer rehearsal must next use published
+PyPI 1.1.11 as its actual planner and a PR-built target wheel in a disposable
+copy: A-to-B, B chat switch, content merge and post-merge-check without refresh,
+B-to-A return, and direct 1.1.10-to-B completion. This rehearsal is NOT_RUN here;
+owner acceptance is PENDING. Self-built local wheels do not replace that proof.
+
+## Complexity balance
+
+B activates existing modular rendering, byte comparison and runtime identity;
+it adds no production module, third-party dependency, public command or generic
+workflow framework. The only additional production behavior beyond activation
+is a more precise advisory for installed versions below 1.1.11. Tests preserve
+the independent A path and B default. Existing typed results and evidence are
+sufficient; an additional DCO cell layer would add complexity here.
+
+The existing retest adapter also needs two bounded fixture corrections under
+the B default: skip an empty migration commit when init already produced the
+same v2 bytes, and remove the caller's PYTHONPATH before checking the owned
+returned A-prime runtime. Existing 084/094 and 097/098 contracts reproduced the
+failures. Their expectations and the real wheel-transition code remain unchanged.
+The adapter's existing mixed fixture-dispatch responsibilities remain; no new
+framework or broader runner extraction is introduced in this activation slice.
+
+For external workspaces, an unchanged captured-input set after a content merge
+no longer needs a refresh-only PR. Chat switches leave the versioned handoff
+files byte-identical: changing HEAD, branch, time and run identity belongs to
+the ignored runtime record, so it produces no tracked handoff diff. Physical
+runtime evidence is preserved, not deleted. Changed authority inputs still
+require governed regeneration. Self-hosting keeps its existing C4 lifecycle.
+Legacy v1 compatibility is retained until KIT-GF-096; it is not removed now.
+No measured CI/runtime saving or productive consumer verification is claimed.
+
+The repository version remains 1.1.11; no B release version is assigned. The
+existing test-wheel builder can give the PR target a distinct disposable test
+version. Its synthetic A wheel must not replace the published PyPI 1.1.11
+planner in the independent rehearsal. Main and all published artifacts remain
+unchanged; this activation stays on the unmerged PR branch.
+
+## Rebase verification, 2026-11-02
+
+After GF-099 #2724 and complete post-merge handoff #2725, all three B commits
+were rebased onto daa14918. The implementation head acd77b9b passed the full
+suite (4,526 tests, 560 warnings, 393.48 seconds), fresh installed-wheel
+contracts 094/095/097/098/099 and all local gates. Original source/test changes
+and main's GF-099 code are preserved byte-for-byte.
+
+The [KIT-GF-100 rebase report](KIT-GF-100-rebase-detached-head-resolver-2026-11-02.md)
+records exact Git continuation, all affected paths, the complete implementation
+range-diff, total diff review and a separate isolated negative resolver probe.
+100 is OPEN; its fix is not part of B. The guide and changelog now describe
+release semantics; the current draft/merge/release hold stays in #2723.
+Published-A consumer rehearsal and owner acceptance are still pending.
diff --git a/docs/reports/greenfield/KIT-GF-100-rebase-detached-head-resolver-2026-11-02.json b/docs/reports/greenfield/KIT-GF-100-rebase-detached-head-resolver-2026-11-02.json
new file mode 100644
index 00000000..b1880d29
--- /dev/null
+++ b/docs/reports/greenfield/KIT-GF-100-rebase-detached-head-resolver-2026-11-02.json
@@ -0,0 +1,61 @@
+{
+  "finding": "KIT-GF-100",
+  "expected": "BLOCKED_CURRENT_BRANCH_MISSING",
+  "result": "REPRODUCED",
+  "resolver_returncode": 2,
+  "resolver": {
+    "schema_version": 1,
+    "kind": "transfer_conflict_resolve_file_result",
+    "action": "conflict-resolve-file",
+    "result_status": "BLOCKED",
+    "final_signal": "f",
+    "branch": "",
+    "path": "example.txt",
+    "source": "resolved.txt",
+    "blockers": [
+      "current_branch_missing"
+    ],
+    "unmerged_files": [
+      "example.txt"
+    ],
+    "steps": [
+      {
+        "name": "current-branch",
+        "argv": [
+          "git",
+          "branch",
+          "--show-current"
+        ],
+        "returncode": 0,
+        "stdout": "",
+        "stderr": "",
+        "ok": true
+      },
+      {
+        "name": "unmerged-files",
+        "argv": [
+          "git",
+          "diff",
+          "--name-only",
+          "--diff-filter=U"
+        ],
+        "returncode": 0,
+        "stdout": "example.txt\n",
+        "stderr": "",
+        "ok": true
+      }
+    ],
+    "next_action": "Inspect conflict-resolve-file blockers before continuing: current_branch_missing"
+  },
+  "conflicted_file_unchanged": true,
+  "unmerged_files": [
+    "example.txt"
+  ],
+  "fixture": "isolated synthetic local Git rebase; no actual PR or branch mutation",
+  "schema_version": 1,
+  "negative_machine_contract": {
+    "result": "PASS",
+    "steps": 19,
+    "scope": "Negative reproduction and unchanged conflict bytes/index only; does not prove successful resolution or close the OPEN finding."
+  }
+}
diff --git a/docs/reports/greenfield/external-findings-status.json b/docs/reports/greenfield/external-findings-status.json
index ab47e2b9..04e6f5be 100644
--- a/docs/reports/greenfield/external-findings-status.json
+++ b/docs/reports/greenfield/external-findings-status.json
@@ -1,10 +1,10 @@
 {
   "authority": "Kit adjudication; VERIFIED_FIXED belongs to the consuming workspace",
   "counts": {
-    "CLOSED": 98,
+    "CLOSED": 99,
     "NOT_APPLICABLE": 0,
     "OPEN": 1,
-    "PARTIAL": 1
+    "PARTIAL": 0
   },
   "execution_classes": {
     "kit_release": 7,
@@ -7588,14 +7588,14 @@
         "remote_effects": [
           "none"
         ],
-        "verification": "Implementation retained behind the package activation constant. Release A remains v1; GF-094 becomes effective only in separately approved release B. Consumer rehearsal and owner acceptance remain required.",
+        "verification": "This local machine contract is not consumer acceptance. Independent published-PyPI-A rehearsal, local return and owner acceptance are recorded in the linked release-prerequisite report; consumer VERIFIED_FIXED remains independent.",
         "workspace_kind": "external_manifest"
       },
       "fixed_in": "unreleased",
       "id": "KIT-GF-094",
-      "kit_state": "PARTIAL",
+      "kit_state": "CLOSED",
       "prs": [],
-      "report": "docs/reports/greenfield/KIT-GF-094-external-handoff-v2-2026-11-01.md"
+      "report": "docs/reports/greenfield/KIT-GF-094-release-b-activation-2026-11-01.md"
     },
     {
       "external_retest": {
@@ -8442,5 +8442,5 @@
   "kind": "external_findings_status",
   "machine_contracts": 59,
   "schema_version": 1,
-  "source_sha256": "b564f951720c16cf7cab1b034a5d3f47127b5aef17ca8f839703f97169a143c9"
+  "source_sha256": "76ed5e84bb6bd4479d1ebb53824d0747220af758cf4e9fcdf194e791a5810e7a"
 }
diff --git a/src/agentic_project_kit/external_projection_policy.py b/src/agentic_project_kit/external_projection_policy.py
index 5f2a337b..291bb9c9 100644
--- a/src/agentic_project_kit/external_projection_policy.py
+++ b/src/agentic_project_kit/external_projection_policy.py
@@ -4,7 +4,7 @@ from pathlib import Path
␠
 from agentic_project_kit.workspace_detection import is_external_manifest_workspace
␠
-EXTERNAL_PROJECTION_V2_ACTIVE = False
+EXTERNAL_PROJECTION_V2_ACTIVE = True
␠
␠
 def external_projection_contract_version() -> int:
diff --git a/src/agentic_project_kit/greenfield_retest.py b/src/agentic_project_kit/greenfield_retest.py
index e57c93a5..d76dbda0 100644
--- a/src/agentic_project_kit/greenfield_retest.py
+++ b/src/agentic_project_kit/greenfield_retest.py
@@ -368,7 +368,15 @@ def _fixture(machine: dict[str, Any], base: Path, env: dict[str, str], stack=Non
         result = _run(["agentic-kit", "transfer", "prepare-successor-handoff", "--json"], root, env)
         if result.returncode:
             return root, variables, ["active v2 fixture generation failed: " + result.stderr[-400:]]
-        steps = [["git", "add", "."], ["git", "commit", "-m", "Active B fixture"]]
+        result = _run(["git", "add", "."], root, env)
+        if result.returncode:
+            return root, variables, ["active v2 fixture staging failed: " + result.stderr[-400:]]
+        staged = _run(["git", "diff", "--cached", "--quiet"], root, env)
+        if staged.returncode not in {0, 1}:
+            return root, variables, ["active v2 fixture diff failed: " + staged.stderr[-400:]]
+        # B init already renders v2. Preparing identical inputs is a no-op,
+        # whereas an A-created fixture still needs its actual migration commit.
+        steps = [["git", "commit", "-m", "Active B fixture"]] if staged.returncode else []
         if machine.get("origin"):
             # Match the existing release fixture: construct only the confined
             # disposable bare origin, without a protected-branch push.
@@ -389,6 +397,9 @@ def _fixture(machine: dict[str, Any], base: Path, env: dict[str, str], stack=Non
             root = base / "transition/consumer"
             (root / ".agentic/tmp/transition-proof.json").write_text(json.dumps(proof, sort_keys=True))
             env["AGENTIC_KIT_RETEST_PYTHON"] = str(root / ".venv/bin/python")
+            # As for other owned runtimes, never let the extracted caller's
+            # PYTHONPATH override the wheel installed in the fixture runtime.
+            env.pop("PYTHONPATH", None)
         except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, AssertionError) as exc:
             return root, variables, [f"real wheel transition failed: {exc}"]
     return root, variables, []
diff --git a/src/agentic_project_kit/kit_release_check.py b/src/agentic_project_kit/kit_release_check.py
index 44e2a171..324d7304 100644
--- a/src/agentic_project_kit/kit_release_check.py
+++ b/src/agentic_project_kit/kit_release_check.py
@@ -208,12 +208,12 @@ def check_release(root: Path, *, installation: dict | None = None, fetch=None) -
                 else "AHEAD"
             ),
         )
-        if result["result"] == "UPDATE_AVAILABLE" and installed <= Version("1.1.10") and Version(latest) > Version("1.1.10"):
+        if result["result"] == "UPDATE_AVAILABLE" and installed < Version("1.1.11") and Version(latest) >= Version("1.1.11"):
             result["transition_guidance"] = (
-                "Install the documented expand release A before the v2 activation release B. "
+                "Install release A (1.1.11) before the v2 activation release B. "
                 "A supplies the migration planner and adoption evidence needed for governed return. "
                 "After a direct legacy-to-B attempt, use prepare-successor-handoff and repeat kit update; "
-                "missing original adoption evidence cannot be reconstructed."
+                "missing original adoption evidence cannot be reconstructed, so no governed installation return is available."
             )
     except (OSError, ValueError, KeyError, TypeError, RecursionError) as exc:
         reason = (
diff --git a/src/agentic_project_kit/reference/external-findings-status.json b/src/agentic_project_kit/reference/external-findings-status.json
index ab47e2b9..04e6f5be 100644
--- a/src/agentic_project_kit/reference/external-findings-status.json
+++ b/src/agentic_project_kit/reference/external-findings-status.json
@@ -1,10 +1,10 @@
 {
   "authority": "Kit adjudication; VERIFIED_FIXED belongs to the consuming workspace",
   "counts": {
-    "CLOSED": 98,
+    "CLOSED": 99,
     "NOT_APPLICABLE": 0,
     "OPEN": 1,
-    "PARTIAL": 1
+    "PARTIAL": 0
   },
   "execution_classes": {
     "kit_release": 7,
@@ -7588,14 +7588,14 @@
         "remote_effects": [
           "none"
         ],
-        "verification": "Implementation retained behind the package activation constant. Release A remains v1; GF-094 becomes effective only in separately approved release B. Consumer rehearsal and owner acceptance remain required.",
+        "verification": "This local machine contract is not consumer acceptance. Independent published-PyPI-A rehearsal, local return and owner acceptance are recorded in the linked release-prerequisite report; consumer VERIFIED_FIXED remains independent.",
         "workspace_kind": "external_manifest"
       },
       "fixed_in": "unreleased",
       "id": "KIT-GF-094",
-      "kit_state": "PARTIAL",
+      "kit_state": "CLOSED",
       "prs": [],
-      "report": "docs/reports/greenfield/KIT-GF-094-external-handoff-v2-2026-11-01.md"
+      "report": "docs/reports/greenfield/KIT-GF-094-release-b-activation-2026-11-01.md"
     },
     {
       "external_retest": {
@@ -8442,5 +8442,5 @@
   "kind": "external_findings_status",
   "machine_contracts": 59,
   "schema_version": 1,
-  "source_sha256": "b564f951720c16cf7cab1b034a5d3f47127b5aef17ca8f839703f97169a143c9"
+  "source_sha256": "76ed5e84bb6bd4479d1ebb53824d0747220af758cf4e9fcdf194e791a5810e7a"
 }
diff --git a/tests/test_external_projection_activation.py b/tests/test_external_projection_activation.py
index 3e85718b..e9d0db04 100644
--- a/tests/test_external_projection_activation.py
+++ b/tests/test_external_projection_activation.py
@@ -31,7 +31,17 @@ def test_external_generation_and_init_follow_one_package_policy(tmp_path, monkey
     assert result.validation_report["status"] == "PASS"
␠
␠
-def test_release_a_default_is_not_an_implicit_migration(tmp_path):
+def test_shipped_default_is_projection_v2():
+    from agentic_project_kit.external_projection_policy import external_projection_contract_version
+    from agentic_project_kit.kit_update import _INVENTORY
+
+    assert external_projection_contract_version() == 2
+    inventory = subprocess.run([sys.executable, "-I", "-c", _INVENTORY], capture_output=True, text=True, check=True)
+    assert json.loads(inventory.stdout)["projection_contract_version"] == 2
+
+
+def test_release_a_default_is_not_an_implicit_migration(tmp_path, monkeypatch):
+    monkeypatch.setattr("agentic_project_kit.external_projection_policy.EXTERNAL_PROJECTION_V2_ACTIVE", False)
     from agentic_project_kit.external_projection_policy import external_projection_contract_version
     from agentic_project_kit.workspace_init import build_workspace_init_plan, execute_workspace_init
     from agentic_project_kit.checks import check_all
@@ -41,18 +51,30 @@ def test_release_a_default_is_not_an_implicit_migration(tmp_path):
     assert check_all(tmp_path) == []
␠
␠
-def test_release_a_target_probes_do_not_treat_module_presence_as_activation():
+def test_release_a_target_probes_do_not_treat_module_presence_as_activation(monkeypatch):
+    monkeypatch.setattr("agentic_project_kit.external_projection_policy.EXTERNAL_PROJECTION_V2_ACTIVE", False)
     from agentic_project_kit.kit_update import _INVENTORY
     from agentic_project_kit.kit_update_projection import TARGET_PROJECTION_PREVIEW
␠
-    inventory = subprocess.run([sys.executable, "-I", "-c", _INVENTORY], capture_output=True, text=True, check=True)
+    # -I starts a separate interpreter; scope the same A policy explicitly
+    # inside that process rather than adding a production environment switch.
+    def release_a_script(script):
+        return (
+            "from unittest.mock import patch\n"
+            "from agentic_project_kit import external_projection_policy as policy\n"
+            "with patch.object(policy, 'EXTERNAL_PROJECTION_V2_ACTIVE', False):\n"
+            f"    exec({script!r})\n"
+        )
+
+    inventory = subprocess.run([sys.executable, "-I", "-c", release_a_script(_INVENTORY)], capture_output=True, text=True, check=True)
     assert json.loads(inventory.stdout)["projection_contract_version"] == 1
-    preview = subprocess.run([sys.executable, "-I", "-c", TARGET_PROJECTION_PREVIEW], capture_output=True, text=True)
+    preview = subprocess.run([sys.executable, "-I", "-c", release_a_script(TARGET_PROJECTION_PREVIEW)], capture_output=True, text=True)
     assert preview.returncode == 0, preview.stderr
     assert json.loads(preview.stdout) == {"supported": False, "files": {}}
␠
␠
 def test_release_a_update_records_adoption_without_a_projection_migration(tmp_path, monkeypatch):
+    monkeypatch.setattr("agentic_project_kit.external_projection_policy.EXTERNAL_PROJECTION_V2_ACTIVE", False)
     from pathlib import Path
     import runpy
     from agentic_project_kit import kit_return
@@ -75,6 +97,7 @@ def test_release_a_update_records_adoption_without_a_projection_migration(tmp_pa
␠
␠
 def test_release_a_malformed_return_evidence_is_a_structured_stop(tmp_path, monkeypatch):
+    monkeypatch.setattr("agentic_project_kit.external_projection_policy.EXTERNAL_PROJECTION_V2_ACTIVE", False)
     from agentic_project_kit.transfer_repo_actions import post_merge_check
     path = tmp_path / ".agentic/kit-update/ledger.jsonl"
     path.parent.mkdir(parents=True)
diff --git a/tests/test_kit_release_check.py b/tests/test_kit_release_check.py
index 3c37c10b..4193150a 100644
--- a/tests/test_kit_release_check.py
+++ b/tests/test_kit_release_check.py
@@ -56,13 +56,24 @@ def test_release_relation(root, installed, expected):
     assert urls == ["https://pypi.org/simple/agentic-project-kit/"]
␠
␠
-def test_legacy_update_notice_prefers_expand_release_before_v2(root):
+@pytest.mark.parametrize("installed", ["1.1.10", "1.1.10.post1"])
+def test_legacy_update_notice_prefers_expand_release_before_v2(root, installed):
     result = release.check_release(
-        root, installation={"installed": "1.1.10", "installation_kind": "wheel"},
+        root, installation={"installed": installed, "installation_kind": "wheel"},
         fetch=lambda url: index(("1.1.12", False)),
     )
     assert "release A" in result["transition_guidance"]
     assert "adoption evidence" in result["transition_guidance"]
+    assert "1.1.11" in result["transition_guidance"]
+    assert "no governed installation return" in result["transition_guidance"]
+
+
+def test_release_a_has_no_legacy_transition_notice(root):
+    result = release.check_release(
+        root, installation={"installed": "1.1.11", "installation_kind": "wheel"},
+        fetch=lambda url: index(("1.1.12", False)),
+    )
+    assert "transition_guidance" not in result
␠
␠
 def test_post_release_wins_over_final_but_not_prerelease_or_yanked():
diff --git a/tests/test_release_greenfield_stamp.py b/tests/test_release_greenfield_stamp.py
index 260aa55a..deb7977c 100644
--- a/tests/test_release_greenfield_stamp.py
+++ b/tests/test_release_greenfield_stamp.py
@@ -14,11 +14,17 @@ from test_release_run import FakeRunner, _workspace
 ROOT = Path(__file__).resolve().parents[1]
␠
␠
-def test_expand_release_defers_gf094_and_its_activation_expiry():
+def test_b_catalog_makes_gf094_eligible_only_for_future_release_stamping():
+    from packaging.version import Version
+    from agentic_project_kit import __version__
+
     data = json.loads((ROOT / CATALOG).read_bytes())
     findings = {f["id"]: f for f in data["findings"]}
-    assert findings["KIT-GF-094"]["kit_state"] == "PARTIAL"
-    assert findings["KIT-GF-094"]["fixed_in"] == "unreleased"
+    assert findings["KIT-GF-094"]["kit_state"] == "CLOSED"
+    fixed = findings["KIT-GF-094"]["fixed_in"]
+    # Preparation is unreleased; the same regression must also allow the
+    # subsequent real B stamp, while permanently excluding released A.
+    assert fixed == "unreleased" or (fixed == __version__ and Version(fixed) > Version("1.1.11"))
     assert "release B" in " ".join(findings["KIT-GF-096"]["external_retest"]["preconditions"])
␠
␠
@@ -42,6 +48,21 @@ def prepare(root, dry_run=False):
                                  summary_lines=SUMMARY_LINES, dry_run=dry_run)
␠
␠
+def test_expand_release_defers_gf094_without_losing_other_closed_fixes(tmp_path):
+    from agentic_project_kit.release_greenfield_stamp import plan_stamp
+
+    root = _copy_release_state_files(tmp_path)
+    data = catalog_fixture(root)
+    findings = {f["id"]: f for f in data["findings"]}
+    findings["KIT-GF-094"].update(kit_state="PARTIAL", fixed_in="unreleased")
+    findings["KIT-GF-095"].update(kit_state="CLOSED", fixed_in="unreleased")
+    (root / CATALOG).write_bytes(encoded(data))
+    plan = plan_stamp(root, TARGET_VERSION)
+    assert "KIT-GF-094" not in plan["finding_ids"]
+    assert "KIT-GF-095" in plan["finding_ids"]
+    assert json.loads((root / CATALOG).read_bytes())["findings"] == data["findings"]
+
+
 def test_prepare_plans_then_stamps_only_closed_unreleased_and_exports(tmp_path):
     root = _copy_release_state_files(tmp_path)
     data = catalog_fixture(root)
@@ -121,6 +142,7 @@ def test_external_v2_release_requires_return_rehearsal_and_owner_acceptance(tmp_
     report.write_bytes(encoded({"release_prerequisites": states}))
     plan = plan_stamp(root, TARGET_VERSION)
     assert plan["release_prerequisites_sha256"]
+    assert "KIT-GF-094" in plan["finding_ids"]
     states["local_return"] = "FAIL"
     report.write_bytes(encoded({"release_prerequisites": states}))
     with pytest.raises(ValueError, match="local_return"):

```
