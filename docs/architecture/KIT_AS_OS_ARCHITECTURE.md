# Agentic Project Kit as an Operating Layer for Arbitrary GitHub Projects

Status: ACCEPTED (v4, angenommen 2026-07-04) — P1 foundation implemented
(workspace resolver, implicit legacy profile, workspace lock); P2+ proceed
on maintainer signal. v0.4.12 release and DOI closeout are complete (release
tag `v0.4.12`, version DOI `10.5281/zenodo.21135030`).
Proposed repo location: `docs/architecture/KIT_AS_OS_ARCHITECTURE.md`
(register via `agentic-kit doc-registry register`; the adopting PR carries
documentation only, no code).
Scope: architecture and migration strategy only.

Review provenance: v2 corrected a factual error from v1 (a claimed-absent
`init` command that exists); v3 incorporated sequencing, evidence discipline,
status projection, and the activity-log boundary; v4 closes four boundary/
lifecycle gaps (CI entry point, schema upgrade path, legacy-fallback
lifetime, workspace locking).

---

## 1. Vision

Today the kit is **dogfooded primarily in its own repository**, and many
governance paths still assume that repository's layout. The goal is to let
the same engine govern **any** GitHub project — new or pre-existing — without
copying the kit into that project. A user installs the kit once, points it at
a repository, and gets the full governance surface there: gates, audits,
transfer protocol, work cycle, safety classes, registries, GUI cockpit.

The founding constraints are unchanged: local, deterministic, repo-backed,
machine-checkable, operable at chat-subscription cost with no coding-API
dependency.

## 2. The two operating modes (the sentence this document hinges on)

> This architecture introduces a **second operating mode** of the kit. It does
> not replace the existing project-generator mode. **Generator mode** may
> create a repository skeleton; **operating-layer mode** governs an existing
> repository through a reserved `.agentic/` workspace.

**Generator mode — exists today.** `agentic-kit init <name>` (plus the
`scaffold` command group) creates a new project skeleton: `AGENTS.md`,
`docs/PROJECT_START.md`, `docs/STATUS.md`, gates docs, CI workflows,
PR templates, pre-commit config, package/test skeleton. By design it writes
*outside* any namespace — creating those files **is** its purpose. This mode
is kept, untouched, under its existing name; its meaning space is protected.

**Operating-layer mode — new.** An existing repository is placed under kit
governance without rewriting its code or documents. In this mode the kit
writes only inside `.agentic/` and narrowly documented, explicitly invoked
setup files (`.gitignore`; optional CI injection, see §7.3) — unless the user
explicitly invokes a guarded scaffolding or migration command. Explicit,
user-invoked commit/push of the user's own work through the guarded wrappers
is unaffected; *governance artifacts* stay inside the namespace.

## 3. The core decision: kernel, precisely framed

The engine is a **kernel**: project-agnostic at the center, everything
target-specific supplied from outside. One deliberate sharpening: an OS boots
first and owns the machine; the kit is a **guest** in a repository it does not
own. The metaphor that steers implementation is the **git / pre-commit / tox
class of tool** — installed outside every repo, leaving inside only a reserved
namespace and a declarative manifest.

### 3.1 Alternatives considered and rejected

**Copy/template model.** Every kernel improvement needs backporting into every
derived repo; kit and project code interleave. (Generator mode is *not* this —
it stamps a skeleton once; it does not fork the kernel.)

**GitHub App / bot service.** Contradicts local/deterministic/no-service
founding constraints; moves enforcement away from the developer's machine.

**Git submodule / subtree.** Version-coupling fragility; vendoring in
different clothes.

**CI-only distribution.** Discards GUI, guided work cycle, and transfer
protocol — the didactic heart. Retained only as an optional layer: a CI
recipe running the same deterministic gates server-side (entry point defined
in §7.3, not left implicit).

## 4. Layer model

```
┌────────────────────────────────────────────────────────────┐
│ L3  Interfaces: CLI · GUI cockpit · LLM transfer · (CI)    │
├────────────────────────────────────────────────────────────┤
│ L2  Modules & profiles: gate profiles · feature toggles ·  │
│     project-type adapters (pyproject / package.json / none)│
├────────────────────────────────────────────────────────────┤
│ L1  Workspace (inside the TARGET repo): .agentic/          │
│     config.yaml manifest · registries · rules · state ·    │
│     transfer · tmp (incl. workspace lock)                  │
├────────────────────────────────────────────────────────────┤
│ L0  Kernel (pip package, outside every target repo)        │
└────────────────────────────────────────────────────────────┘
```

Hard rules:

1. **L0 contains no target-repository-specific knowledge.** It may ship
   generic profile defaults (`python-default`, `generic`, and the *implicit
   legacy profile*, see §8), but all target-specific paths, toggles, and
   policy choices resolve from the L1 manifest.
2. **Operating-layer mode writes only inside `.agentic/`** plus narrowly
   documented, explicitly invoked setup files (`.gitignore`; opt-in CI
   injection per §7.3); generator mode is exempt by purpose (§2).
3. **L2 is data, not forks.** Profiles are configuration the kernel
   interprets; toggling a module never copies kernel code.
4. **L3 talks to L0 only through the public CLI/API.** The GUI stays a thin
   subprocess shell; no interface acquires private kernel bypasses.
5. **No new permission model.** The operating layer reuses the existing
   cockpit/action safety model verbatim: READ_ONLY / BOUNDED / DESTRUCTIVE
   enforced kernel-side, access levels as visibility-never-permission,
   dry-run-before-confirm with signature protection, main-mutation refusal,
   `ensure_remote_head` before PR creation. This architecture is a
   consequent continuation of that model, not a new vision.
6. **Activity logs are UI/evidence views, not project state.** The cockpit's
   activity log records local command/result events. It is local by default
   (`.agentic/tmp/audit/`) and must not become semantic project memory unless
   explicitly exported as evidence.
7. **Mutations are serialized per workspace.** Because L3 interfaces are
   independent processes over the same L1 workspace (the GUI itself invokes
   the CLI as subprocesses), concurrent mutation is the normal case, not an
   edge case. The kernel serializes mutating operations through a workspace
   lock (§5.5); this covers workspace-state writes, git worktree/history
   mutations, and remote git/GitHub mutations. Read-only status, audit, and
   report-only operations never take the lock.

## 5. The workspace: `.agentic/`

### 5.1 Existing foothold

The namespace already exists on `main`: `transfer/inbox/current.yaml` as the
canonical carrier on the `gui-transfer-tasks` ref (legacy transfer path
removed), `transfer/outbox/`, `rule_ack/`. This document formalizes and
completes a begun namespace.

### 5.2 Target layout and visibility policy

```
.agentic/
├── config.yaml            # manifest — versioned
├── registries/            # doc + rule registries — versioned
├── rules/                 # rule capsules, comm rules — versioned
├── ci/                    # CI recipe templates (source of truth) — versioned
├── state/
│   ├── status.md          # project-governance status; may be PROJECTED to
│   │                      # a public docs/STATUS.md — projection, not a
│   │                      # forced physical move (see P5)
│   └── handoff/           # validated handoff packages only — versioned
├── transfer/              # visibility is MODE-DEPENDENT, see below
│   ├── inbox/
│   └── outbox/
└── tmp/                   # ALWAYS git-ignored
    ├── workspace.lock     # mutation lock (§5.5)
    ├── (wrapper status, panel state)
    └── audit/             # activity-log exports
```

**Transfer visibility is mode-dependent, not absolute.** In **file-transfer
mode the versioned, pushed carrier IS the communication channel**: `SEND`
commits the carrier and pushes it to the dedicated `gui-transfer-tasks` ref
precisely so an LLM without API access can read it through GitHub;
`remote_readable=true` is the success condition. A blanket git-ignore default
would break that mechanism. Therefore the manifest decides:

```yaml
transfer:
  visibility: repo    # file-transfer mode: carrier versioned & pushed (default)
  # visibility: local # remote/copy-paste-only projects: transfer git-ignored
```

### 5.3 Private/public boundary

Regardless of mode: **no secrets, credentials, private chat fragments, or
personal logs belong in any versioned part of `.agentic/`.** The task carrier
contains the work order the user knowingly publishes — `SEND` already makes
the push explicit. Machine-local state lives under `.agentic/tmp/` and is
ignored by construction. `workspace adopt` and `workspace init` must print
this boundary; documentation for public target repos must repeat it.

### 5.4 The manifest

```yaml
kit_schema_version: 1        # kernel refuses unknown schema, loudly — but
                             # never without an exit: see workspace upgrade
project: { name: my-project, type: python }   # python | node | generic
profile: python-default
modules: { release_governance: true, doc_registry: true,
           rule_registry: true, transfer: true }
transfer: { visibility: repo }
paths:   { docs_root: docs/ }         # overrides; profile defaults exist
gates:   { extra: [], skip: [] }      # skips are audited, never silent
```

### 5.5 Concurrency: the workspace lock

Multiple kernel processes over one workspace are the *normal* operating
condition (open GUI plus CLI calls plus transfer wrappers). Therefore, from
P1 onward:

- Every **mutating** kernel operation (state writes, registry writes, gate
  runs that record results, transfer sends) acquires
  `.agentic/tmp/workspace.lock` before touching the workspace and releases it
  after. Lock content: `{pid, command, acquired_at}`.
- **Read-only operations never take the lock** — status views, audits in
  report mode, `adopt` stay lock-free by construction.
- **Stale-lock handling:** if the recorded PID no longer exists, the lock is
  taken over with a logged warning; if it exists, the second process fails
  fast with a clear message naming the holder ("workspace is busy:
  <command> pid <n> since <t>") instead of corrupting state.
- **Reentrancy mode:** the normative target is same-PID reentrancy. If a
  process that already holds the workspace lock calls another mutating
  primitive in the same workspace, the nested acquire is a no-op for that PID
  and the outer lock owner remains responsible for the final release. A live
  lock held by a different PID still fails fast. This keeps directly invoked
  primitives protected while allowing orchestrators to call protected
  primitives without self-deadlock.
- The same-PID rule is chosen over a top-level-only contract because LC1 found
  already protected primitives (`branch_create`, `commit_paths`,
  `push_current`) and unprotected orchestrators that can call them
  (`pr_create`, `admin_refresh_pr`, and PR completion flows). Making only the
  top-level wrappers lock would leave direct CLI primitive calls unprotected;
  making every primitive lock without same-PID reentrancy would deadlock nested
  mutation flows.
- The lock holder is the sole writer of wrapper live status for the locked
  section. Nested same-PID operations may contribute local step detail, but
  must not publish a conflicting holder, phase, or `safe_to_interrupt` signal.
  This complements the live-status signal; it does not replace lock ownership.
- The lock is machine-local (under git-ignored `tmp/`), simple (atomic
  create), and complements — not replaces — the existing wrapper live-status
  `safe_to_interrupt` signal.
- Coverage remediation for the LC1 gap classes is tracked as
  `lock-coverage-remediation` (LC3). Until that slice, the audit remains
  report-only and standard gates stay unchanged.

## 6. The two governance spaces and the litmus test

Kernel quality (the kit repo's own tests, releases, CHANGELOG) ships with the
package. Project governance lives entirely in the target repo's `.agentic/`.
**Litmus test:** after migration the kit repository manages itself through
its own workspace like any other project.

## 7. Adoption and lifecycle commands

The existing `agentic-kit init` is the documented **project generator**
(README quickstart) and keeps that role. The operating-layer commands live
under the `workspace` namespace:

### 7.1 `workspace adopt` (READ_ONLY)

Analyzes an existing repo: project type from `pyproject.toml`/`package.json`,
docs tree, existing CI; proposes a manifest and profile; lists docs it
*could* register (reusing `doc-registry check-unregistered` as discovery
engine); reports exactly what `workspace init` would create. Changes nothing
by construction.

### 7.2 `workspace init` (BOUNDED, dry-run default)

Creates `.agentic/` with manifest, empty registries, the `.agentic/tmp/`
ignore rule, `.agentic/state/status.md`, `.agentic/state/handoff/`, CI recipe
templates under `.agentic/ci/`, and a repo-parameterized initial LLM prompt.
Refuses if a foreign `.agentic/` already exists (no silent merge). `--execute`
required to write; never touches files outside the namespace and `.gitignore`
(CI injection is a separate opt-in, §7.3). Bulk-registering discovered docs
stays a separate, explicit, additive step.

### 7.3 CI and hook entry points (the "bootloader" decision)

Without an entry point into existing CI or local hooks, the operating layer
stays passive until manually invoked. The architectural decision:

- **Default: instruct, don't inject.** `workspace init` writes the CI recipe
  (e.g. a GitHub Actions job running `standard-gates-audit-suite`) and a
  pre-commit snippet into `.agentic/ci/` as versioned **templates**, and
  prints copy-paste instructions. The user wires them in. This keeps rule 2
  intact by default.
- **Opt-in injection:** `workspace init --inject-ci` (and
  `--inject-pre-commit`) is the narrowly documented, explicitly invoked
  exception — BOUNDED, covered by the dry-run/execute pattern — that copies
  the template to `.github/workflows/agentic-gate.yaml` (respectively appends
  the pre-commit hook). The dry-run names the exact files it would create;
  refusal if they already exist (no silent overwrite).
- `.agentic/ci/` stays the **source of truth**; injected copies carry a
  header pointing back to it.

### 7.4 `workspace upgrade` (BOUNDED, dry-run default)

The schema gate must fail loudly on a version mismatch — but a hard failure
without an exit locks the user out after a kernel update meets an older
manifest. Therefore, mandatory from the first schema bump onward:

- `workspace upgrade` migrates an L1 manifest **deterministically and
  stepwise** (v1→v2→…→current), one documented transformation per schema
  bump, shipped with the kernel.
- Dry-run prints the exact manifest diff; `--execute` writes it and keeps the
  previous manifest as `.agentic/config.yaml.bak.v<N>`.
- Downgrade is out of scope (an older kernel meeting a newer manifest fails
  with the message "upgrade the kit"); the failure text of the schema gate
  always names `workspace upgrade` as the way forward.

## 8. Technical keystone: the workspace resolver

**Design assumption (to be confirmed by a path-literal audit before
implementation):** current evidence suggests many governance paths are
hardwired or legacy-layout-based, unevenly distributed — the status audit
carries many literals while `doc_registry` already resolves through its core
module and carries none. No central path layer exists. One new kernel module:

```python
class Workspace:
    root: Path; config: KitConfig
    def status_path(self) -> Path: ...
    def doc_registry_path(self) -> Path: ...
    def transfer_inbox(self) -> Path: ...
    def tmp(self) -> Path: ...

def load_workspace(root: Path = Path(".")) -> Workspace:
    # No .agentic/config.yaml → IMPLICIT LEGACY PROFILE with today's paths.
```

**The legacy fallback is a profile, not target knowledge — and it is
time-boxed.** Semantically, the fallback is the *implicit legacy profile*:
generic knowledge of the historical default layout, on the same footing as
`python-default` (rule 1 stays intact). To prevent L0 fragmentation it is
explicitly bounded: **supported through the entire 1.x line, removed in
2.0.0.** From 2.0.0 on, `.agentic/config.yaml` is hard-required, and
`workspace init` creates it in seconds for any straggler repo. This document
is the deprecation announcement. P5d makes that announcement executable:
manifest-less repositories emit a suppressible legacy profile deprecation warning,
while manifest-bearing repositories remain quiet.

## 9. Versioning

0.5.x introduces resolver, manifest, `workspace adopt/init` — all
backward-compatible via the implicit legacy profile. **1.0.0 criteria:**
(a) self-hosting litmus passed, (b) `workspace adopt/init` stable on at least
one real external project (candidate: Comm-SCI-Control-private), (c) tested
too-old/too-new `kit_schema_version` failure paths, (d) a tested
`workspace upgrade` transformation exists before (or with) the first schema
bump. **2.0.0:** implicit legacy profile removed; manifest required.

## 10. Migration roadmap (each phase = separately mergeable slices)

**P1 — Resolver foundation + workspace lock.** `workspace.py` + `KitConfig` +
implicit legacy profile; the mutation lock of §5.5; migrate the
highest-literal modules first (status audit). Acceptance: **public behavior
and generated artifacts unchanged for manifest-less repos** (existing test
suite plus artifact comparison), path-literal count in migrated modules → 0,
and lock acquisition covered by tests (busy path, stale takeover).

**P2 — Manifest + schema gate.** Parsing, loud version-mismatch failure whose
message names `workspace upgrade`, profiles `python-default` and `generic`.

**P3 — `workspace adopt`, `workspace init`, `workspace upgrade` skeleton.**
Read-only analysis first, creation second, upgrade mechanism designed (first
real transformation ships with the first schema bump). CI templates under
`.agentic/ci/`; `--inject-ci` as the documented opt-in exception.

**P4 — Namespace completion for manifest-bearing projects.** Registries,
status, rules, tmp resolve into `.agentic/`; legacy profile remains for
manifest-less repos (until 2.0.0).

**P5 — Kit self-hosting, split for safety:**
- **P5a** manifest only: kit repo gains `.agentic/config.yaml`; physical
  paths stay.
- **P5b** resolver-backed aliases: every kit-repo access runs through the
  resolver; physical paths still stable.
- **P5c** optional physical migration, only once all references, docs, and
  tests are resolver-based. Public surfaces like `docs/STATUS.md` may remain
  as **projections** of `.agentic/state/status.md` rather than being moved.
- **P5d** deprecation of legacy top-level paths inside the kit repo, aligned
  with the 2.0.0 removal of the implicit legacy profile. The deprecation
  warning must fire only for manifest-less workspaces and must be suppressible
  during the 1.x compatibility window.

**P6 — Interface follow-ups.** GUI project selection (cockpit on a chosen
root), initial-prompt parameterization per workspace, CI recipe hardening.

## 11. Open questions (decide before the affected phase)

Monorepos (one workspace per repo root in v1; nested out of scope), foreign
`.agentic/` collision (refuse + report, never merge), multi-project GUI
switcher (later UX question), Windows leg for both resolver paths and the
lock's atomic-create semantics before 1.0.

## 12. Evidence policy for current-state claims

v1 carried a hand-asserted "verified appendix" — and one of its claims
("no init exists") was wrong, caused by an over-narrow search pattern. The
consequence is a rule, in the kit's own spirit:

> Current-state claims in this document are **non-authoritative unless backed
> by a machine-generated evidence log** (command inventory dump, path-literal
> audit output, test-list extract), referenced by path. Manual prose claims
> carry no evidential weight. **Until those logs exist, these claims are
> design assumptions, not acceptance evidence.**

A small `workspace evidence` helper (or reuse of existing audits) should
generate these logs before P1 acceptance and whenever this document is
revised.
