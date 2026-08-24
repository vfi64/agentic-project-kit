# Post-v1.0.4 B1 Comm-SCI Setup

Status: B1_SETUP_COMPLETE  
Date: 2026-08-24  
Branch: codex/b1-comm-sci-setup  
Target repository: `vfi64/Comm-SCI-Control-private`  
Boundary: setup only; realbetrieb not started

## Scope

This report prepares B1 external realbetrieb. It does not perform Comm-SCI
adoption, create or push a Comm-SCI branch, open a Comm-SCI PR, publish a
release, or claim B1 completion.

B1 remains a long-running evidence program. It becomes `B1_EVALUABLE` only
after the threshold defined in
`docs/reports/POST_V1_0_4_B0_REFRESH_METRIC_DEFINITION_20260824.md` is met.

## Access And Baseline

- GitHub repository access: `gh repo view vfi64/Comm-SCI-Control-private`
  succeeded; repository is private; default branch is `main`.
- GitHub pushed-at timestamp: `2026-05-19T20:12:18Z`.
- Local working copy:
  `/Users/hof/Library/CloudStorage/Dropbox/Privat/GitHub/Comm-SCI-Control-private`.
- Local current branch at setup time: `feature/ui-access-levels-v2`.
- Local HEAD at setup time:
  `743dc7cadb78eeace6412fc8b82de1d955bdd606`.
- Local `origin/main` at setup time:
  `e65d6c8a8c02204420703829a171f9423a5a49bf`.

## Remote Git Backup

Mirror backup path:

```text
/Users/hof/backups/comm-sci-mirror-20260824T0706Z.git
```

Mirror command used explicit HTTPS repository input because the configured
GitHub CLI Git protocol was SSH and the workstation SSH key was not accepted.
The failed SSH attempt did not create a usable backup; the HTTPS mirror did.

Verification:

- `git --git-dir=<mirror> fsck --no-progress`: PASS.
- mirror size: `17M`.
- mirror file count: `22`.
- total refs in mirror: `52`.
- branch refs in mirror: `5`.
- tag refs in mirror: `44`.
- mirror `refs/heads/main`:
  `e65d6c8a8c02204420703829a171f9423a5a49bf`.

The complete mirror ref list is stored locally, not versioned:

```text
/Users/hof/backups/comm-sci-mirror-refs-20260824T0706Z.txt
sha256=bf2ae5a0f97da7b69ba1a0dafcfc5872bfac6e015fcf2e7ae3c8df87ad59a04c
```

## Local Non-Git Inventory

The local non-git inventory is stored locally, not versioned:

```text
/Users/hof/backups/comm-sci-non-git-inventory-20260824T0706Z.txt
sha256=86fdea0ff1d5aac14b1e123bdbe1d56725626c1925a86ba19effcdf71ddcf084
```

Redacted counts from `git status --porcelain --ignored`:

- total status lines: `203`;
- tracked modified local-log/local-history files: `4`;
- ignored paths: `199`;
- stash entries: `3`.

No file contents, secret values, credentials, or personal data were copied into
this repository. The detailed path inventory stays local because the target
repository is private.

## Current Remote Activity Snapshot

At setup time:

- open PR count: `1`;
- merged PR count visible through the first 100 merged PR API results: `1`;
- latest five `main` workflow conclusions: success, success, failure, failure,
  success.

This is context only. It is not a B1 measurement window and must not be used as
the B0 refresh denominator.

## Blocked Operations During B1

Until a later report proves the safety logic is generalized for the external
repository, B1 must not run these mutating operations against Comm-SCI:

- `agentic-kit transfer branch-delete`;
- `agentic-kit transfer delete-merged-work-branch`;
- real-mutation remote branch hygiene;
- `agentic-kit docs lifecycle propose-delete`.

Any proposed unblock must be report-only first and maintainer-adjudicated before
execution.

## Required Logs For Realbetrieb

Every B1 cycle must append to two evidence streams before B2 can be considered.

Friction log fields:

- cycle ID;
- task source;
- start/end timestamps;
- branch and PR, if any;
- Kit commands attempted;
- gates run;
- duration;
- failures and retries;
- manual interventions;
- handoff/successor continuation;
- refresh events by the B0 definition;
- final state.

Bypass log fields:

- timestamp;
- task;
- planned Kit command;
- why the Kit command was not used;
- replacement action;
- friction cost;
- safety impact;
- suspected root cause;
- reproducibility.

## State Decision

B1 setup is complete enough to enter `B1_SETUP_COMPLETE`.

Realbetrieb is not started in this slice. The next B1 work must use a real
Comm-SCI task that would exist without the Kit experiment. One successful setup,
one successful smoke, or one adoption pass is not B1 completion.
