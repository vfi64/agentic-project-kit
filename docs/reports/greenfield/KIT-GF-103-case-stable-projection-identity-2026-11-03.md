# KIT-GF-103 — Case-stable external projection identity

Date: 2026-11-03  
Scope: v2 external successor projection in case-variant clones.  
Status: implementation present on an unreleased feature branch; no merge or release is claimed.

## Finding

The same GitHub repository can have origin URLs whose owner or repository name
differs only by letter case. GitHub treats those names case-insensitively, but
projection v2 copied the spelling from the local origin URL into
`repo.full_name`. A second clone therefore computed different
`repository_name` and `execution_contract` inputs and failed `check` for the
same committed projection.

## Chosen behavior

When a versioned projection already contains a repository name equal to the
origin name without regard to case, the stored spelling is reused. This keeps
existing projection bytes stable and requires no workspace migration. When
there is no matching stored identity, the origin spelling remains the input; a
different repository does not inherit the stored name.

## Regression evidence

The new two-clone regression was run before the fix and failed: the second clone
computed a lower-case name and rendered different bytes. A separate
different-repository control passed before and after the fix.

After the fix, the focused projection, readiness, identity and closeout test
modules passed: `95 passed`. The test checks both rendered byte equality and
`check` PASS in each clone. The local machine contract repeats the case change
through the installed-runtime retest fixture, then confirms `check` PASS and no
tracked projection diff.

## Counterprobe limits

The pre-fix counterprobe is the native regression test run against the original
implementation. The installed-runtime contract verifies the corrected behavior;
no release or external consumer acceptance is inferred from that local result.
