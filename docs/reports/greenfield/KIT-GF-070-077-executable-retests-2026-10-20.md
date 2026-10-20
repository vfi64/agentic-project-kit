---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-070 and KIT-GF-077: executable external retests and remote-next push effects

Date: 2026-10-20
Kit state: KIT-GF-070 PARTIAL, KIT-GF-077 CLOSED in candidate; planned release 1.1.3.
Consumer VERIFIED_FIXED remains independent.

## Observation

- KIT-GF-070: `greenfield status --json` listed argv templates per finding, but the expected
  results were prose for most findings, preconditions were prose and no retest carried a
  machine marker for whether it needs GitHub or a release. A consumer could only re-implement
  the Kit's fixtures or accept returncode 0 as proof, so VERIFIED_FIXED could not be reached
  systematically. The retest of KIT-GF-039 also named a route the Kit never had
  (`transfer communication-context-status`).
- KIT-GF-077 (found while deriving execution classes): the command manifest declared only
  `fetch` for `transfer remote-next` and `transfer remote-work-start`, although both push to
  the transfer or work branch.

## Repair

1. Every catalog retest gets an execution class derived from the installed Kit's command
   manifest, never written by hand: `local` when every route declares only `none`, `fetch` or
   `push` (a disposable workspace with a local bare origin satisfies them), `owner_remote` when a
   route needs GitHub, PyPI or another service, `kit_release` for release retests. The export
   carries `execution_class` and `remote_effects` per retest and class counts.
2. Catalog validation now requires every retest command to name a route of the installed
   manifest with declared options only; the KIT-GF-039 retest names
   `rules require-current-communication-context --json`.
3. A local retest may carry a machine contract: a fixture (`git_repository` or
   `external_manifest`, optionally with a bare origin), steps that run only `agentic-kit` or
   `git`, file edits confined to the fixture, exact expectations (returncode, JSON paths,
   stdout) and captured values such as an approval signature. A contract states what it covers;
   it must run a route of its retest and may not need a remote service.
4. `agentic-kit greenfield retest --id <id> [--id ...] | --all [--json]` runs contracts with the
   installed Kit in a temporary directory with an isolated Git configuration. Per finding:
   PASS, FAIL, NO_MACHINE_CONTRACT (local, no contract) or NOT_RUN_LOCALLY (owner_remote,
   kit_release). Overall PASS only when every selected finding passed; any FAIL gives FAIL
   (exit 1); otherwise INCOMPLETE (exit 3); bad input BLOCKED (exit 2). The result names the Kit
   version, the package location it ran from and the catalog digest. The route is READ_ONLY for
   the workspace and has no remote effect.
5. Machine contracts in this slice: KIT-GF-001, 066, 070, 072, 074, 075, 076 and 077. Each
   contract's `covers` text names what it proves and what stays outside it (for example the
   KIT-GF-072 re-derivation during `kit update`, which needs a release download).
6. The manifest declares `fetch` and `push` for `transfer remote-next` and
   `transfer remote-work-start`; consumers that ask for approval by declared effects see the push.

## Remaining (KIT-GF-070 stays PARTIAL)

The other local retests report NO_MACHINE_CONTRACT until they get contracts in later slices;
owner_remote and kit_release retests need live evidence from a consumer.

## Regression

`tests/test_greenfield_retest.py` runs the installed wheel: every pilot contract PASS, a
contract with a wrong expectation FAIL, unknown routes and options, non-local steps, unbound
placeholders, self-retests and contracts on remote retests rejected, mixed selections
INCOMPLETE with exit 3, the consumer working directory unchanged, and the declared push effects.
