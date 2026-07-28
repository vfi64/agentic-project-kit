# DPA-400 — Renderer Contract

Status: review-ready
Status-date: 2026-07-17
Authority: normative DPA specification; review-ready after independent post-adjudication verification at `6050d0664d9c1ac8bd1a2eb9d6409593046ede9c`

## 1. Purpose

This specification defines the renderer contract for the Document Projection Architecture.

A renderer is a statically resolved, side-effect-free computation that consumes only lifecycle-resolved immutable declared semantic inputs and contract-declared configuration and returns text or bytes for exactly one registered projection target.

This specification extends the existing documentation-management architecture. It does not create a plugin framework, a second registry, a second lifecycle, a command family, a state authority or a write path.

Concrete module names, callable signatures, renderer identifiers and implementation locations remain `NEEDS_MAIN_REPO_VALIDATION` until validated against an exact main-repository ref.

## 2. Normative dependencies

DPA-400 depends on:

- DPA-000 for the canonical invariants;
- DPA-100 for authority, source, configuration, renderer-version, determinism, fingerprint and failure vocabulary;
- DPA-200 for target identity, document forms, partition ownership and target semantics;
- DPA-300 for registry integration, lifecycle phase ordering, immutable plans, stale-plan guards, acceptance state and recovery;
- DPA-ADR-003, DPA-ADR-004, DPA-ADR-005, DPA-ADR-013, DPA-ADR-014, DPA-ADR-016, DPA-ADR-017, DPA-ADR-019 and DPA-ADR-020.

## 3. Scope

DPA-400 owns:

1. renderer identity and static resolution;
2. renderer callable and return contracts;
3. declared semantic inputs;
4. contract-declared configuration;
5. deterministic output requirements;
6. purity and side-effect prohibitions;
7. one-invocation/one-target behavior;
8. payload-only region output;
9. renderer failure classification at the architecture boundary;
10. renderer identifier, interface-version, semantic-version and implementation-evidence obligations;
11. renderer test and conformance obligations.

DPA-400 does not own:

- registry serialization;
- target or partition writes;
- mutation plans;
- locks or workflow serialization;
- acceptance-state persistence;
- lifecycle findings or severity mapping;
- gate outcomes;
- migration-form selection.

## 4. Renderer authority boundary

A renderer has projection authority only for the bytes it computes under one validated projection contract.

A renderer:

- MAY consume lifecycle-resolved immutable canonical-source values or content-addressed immutable snapshots;
- MAY consume lifecycle-resolved immutable contract-declared configuration;
- MUST return text or bytes only;
- MUST NOT write repository files, lifecycle state, registry state, evidence, logs used as runtime authority or acceptance state;
- MUST NOT acquire locks;
- MUST NOT invoke Git, shell commands, network calls, workflow commands or repository mutation APIs;
- MUST NOT assign trust states;
- MUST NOT decide whether output is accepted;
- MUST NOT repair malformed targets or partition boundaries;
- MUST NOT select a document form;
- MUST NOT treat prior projection output, evidence or historical prose as canonical input unless that input is independently declared canonical by another accepted authority contract.

The lifecycle remains the sole caller that may use renderer output for a governed mutation plan.

## 5. Renderer identity and static resolution

### 5.1 Renderer identifier

Every projection contract MUST declare one renderer identifier.

The identifier MUST be:

- stable within its declared compatibility scope;
- declarative;
- reviewable in registry content;
- resolvable through a static mapping owned by reviewed main-repository code;
- included in contract and plan fingerprints.

A renderer identifier MUST NOT be:

- an import path supplied by registry data;
- a shell command;
- a URL;
- an expression;
- a dynamic module or package reference;
- a plugin-discovery entry point;
- a fallback chain.

### 5.2 Static mapping

Renderer resolution MUST use a closed, explicit mapping from renderer identifiers to reviewed implementations.

Unknown identifiers MUST fail loud before rendering and planning.

Duplicate identifiers, ambiguous aliases or environment-dependent resolution MUST fail loud.

The mapping MAY support reviewed aliases only when:

- every alias resolves to exactly one implementation;
- alias semantics are versioned;
- the canonical identity used in fingerprints is unambiguous;
- removal and deprecation follow governed compatibility rules.

The concrete mapping location and callable registration mechanism remain `NEEDS_MAIN_REPO_VALIDATION`.

## 6. Renderer callable contract

A conforming renderer receives an immutable invocation context containing, directly or through bounded value objects:

- the validated projection-contract identity and version;
- exactly one registered target identity;
- ordered lifecycle-resolved immutable source values or content-addressed immutable source snapshots;
- lifecycle-resolved immutable contract-declared configuration;
- target semantics required to shape the payload;
- renderer identifier;
- renderer interface version;
- renderer semantic version.

No invocation-context values beyond this closed list are permitted without an accepted decision and synchronized DPA-100 and DPA-400 changes.

A renderer MUST NOT receive mutable lifecycle, Workspace, registry, lock, Git client, filesystem writer, subprocess, network or gate objects.

The invocation context MUST be sufficient to compute output without ambient repository reads.

A renderer MUST NOT open, re-read or re-resolve mutable repository paths. If a large source is represented by a path-like handle, the lifecycle MUST provide an immutable content-addressed snapshot whose bytes are identical to the bytes fingerprinted before invocation. The renderer MUST NOT discover additional inputs by traversal, globbing or search.

## 7. Declared inputs

### 7.1 Semantic sources

Every semantic input that can change output facts MUST be declared by the projection contract.

The lifecycle MUST resolve and fingerprint declared sources before renderer invocation. The renderer-visible value or snapshot MUST represent exactly those fingerprinted bytes.

A renderer MUST reject or fail when a required source value is absent or structurally invalid. It MUST NOT substitute:

- prior target bytes;
- evidence records;
- historical prose;
- chat memory;
- environment defaults;
- current time;
- unversioned repository state.

### 7.2 Contract-declared configuration

Configuration MAY control representation such as headings, ordering, labels, templates, separators inside renderer-owned payload, optional sections or formatting policy.

Configuration MUST:

- be explicitly declared;
- be immutable for one invocation;
- have a defined schema and version;
- be included in the contract fingerprint when output-affecting;
- not silently own domain facts.

Unknown or malformed configuration MUST fail loud.

### 7.3 Incidental process context

Locale, timezone, working directory, process environment, host platform, hash randomization, filesystem enumeration order and current time MUST NOT affect semantic output unless explicitly declared and versioned as contract configuration.

Where representation legitimately depends on one of these values, the value MUST be captured explicitly and included in the fingerprint domain.

## 8. Output contract

### 8.1 Return type

A successful renderer invocation MUST return exactly one of:

- Unicode text governed by an explicit encoding step in the lifecycle; or
- immutable bytes.

A renderer MUST NOT return:

- a path;
- a file handle;
- a stream unless it is fully materialized into an immutable side-effect-free byte buffer before crossing the renderer boundary;
- a mutation callback;
- a command;
- a lifecycle finding as a substitute for output;
- multiple independently registered targets.

Structured internal values MAY be used inside the renderer implementation, but the renderer boundary exposed to the lifecycle MUST resolve to one text-or-bytes payload.

### 8.2 Complete target output

For a complete-target projection, renderer output represents all renderer-owned target bytes.

The renderer MUST NOT depend on existing target bytes to construct semantic output.

### 8.3 Registered-region output

For a registered-region projection, renderer output represents payload bytes only.

The renderer MUST NOT emit:

- partition markers;
- boundary separators;
- bytes owned by manual or historical regions;
- complete-parent reconstruction bytes outside its registered payload.

The lifecycle combines the payload with validated preserved bytes and the parent-entry `PartitionContract` under DPA-300.

### 8.4 Empty output

Empty output is valid only when target semantics explicitly permit it.

A renderer returning empty output where the contract prohibits it MUST cause validation failure before mutation.

## 9. Determinism and reproducibility

For identical:

- renderer identifier and renderer semantic version;
- renderer interface version compatible with the same invocation contract;
- projection contract;
- declared source values or immutable snapshots;
- contract-declared configuration;
- target-semantics version;

one renderer invocation MUST return byte-equivalent output after the contract-defined text encoding and normalization steps.

A renderer MUST NOT depend on:

- iteration order not fixed by contract;
- random values without a contract-declared fixed seed;
- wall-clock time;
- process IDs;
- temporary paths;
- network availability;
- mutable global state;
- filesystem metadata not declared as a source;
- prior invocation history.

Determinism tests MUST execute the same invocation multiple times in fresh process contexts where practical.

## 10. Purity and side-effect prohibition

A conforming renderer MUST be observationally pure at the architecture boundary.

During invocation it MUST NOT:

1. create, modify or delete files;
2. modify repository or process configuration;
3. mutate input objects;
4. alter global registries or caches whose state affects later semantic output;
5. emit evidence as runtime state;
6. invoke another renderer;
7. start a nested projection refresh;
8. acquire locks;
9. create commits, branches or pull requests;
10. perform network access;
11. invoke subprocesses or shell commands;
12. modify acceptance state or trust state.

Read-only internal memoization MAY be used only when cache identity covers the invocation identity tuple: projection-contract fingerprint, renderer identifier, renderer semantic version, ordered source fingerprints, configuration fingerprint and target-semantics version. Cache loss MUST NOT change output semantics. A cache MUST NOT become canonical state or evidence authority.

## 11. One invocation, one registered target

One renderer invocation MUST compute exactly one registered target identity.

A renderer MUST NOT:

- return a map of multiple targets;
- trigger another renderer;
- orchestrate dependent projections;
- update sibling regions;
- infer additional target identities from source content.

When multiple targets derive from the same canonical sources, each target requires its own registered contract, invocation, plan and lifecycle transition. Workflow orchestration MAY coordinate these refreshes, but the renderers remain independent.

## 12. Renderer identity, versions and fingerprints

Every renderer contract MUST distinguish:

1. **renderer identifier** — the stable declarative key resolved by the closed static mapping;
2. **renderer interface version** — the lifecycle-to-renderer invocation and return-envelope contract;
3. **renderer semantic version** — output-relevant behavior, which MUST change whenever implementation changes can alter output for identical declared inputs;
4. **renderer implementation evidence** — the concrete reviewed implementation identity, such as a commit SHA, retained as evidence only.

The renderer identifier, interface version and semantic version MUST be available before invocation. The renderer semantic version MUST be included in the projection-contract fingerprint, immutable mutation plans and acceptance-state records. The interface version MUST be validated for callable compatibility. Renderer implementation evidence MUST be recorded in mutation evidence but MUST NOT substitute for the semantic version or become fingerprint-relevant merely because unrelated repository commits changed.

The exact serialized representation remains `NEEDS_MAIN_REPO_VALIDATION`.

## 13. Validation before and after rendering

Before invocation, the lifecycle MUST validate:

- the renderer identifier;
- static mapping uniqueness;
- renderer interface-version compatibility;
- renderer semantic-version availability;
- declared source completeness and immutable identity;
- configuration schema and version;
- target semantics;
- target identity;
- partition-contract identity for region targets.

After invocation and before plan capture, the lifecycle MUST validate:

- return type;
- encoding viability;
- empty-output policy;
- normalization rules;
- payload-only behavior for region targets;
- output fingerprint;
- semantic resource-bound policy where governed.

A renderer MUST NOT silently coerce invalid sources or invalid output into a valid-looking projection.

## 14. Failure contract

Renderer failures are explicit non-accepted outcomes.

A renderer invocation may fail because of:

- missing or invalid declared input;
- unknown renderer identifier or incompatible interface or semantic version;
- invalid configuration;
- deterministic computation error;
- invalid output type;
- target-semantics violation;
- detected side effect;
- semantic resource-bound violation;
- operational safety abort.

A failed invocation MAY return a bounded failure envelope containing:

- a stable diagnostic code;
- a human-readable message;
- the identity of the offending declared input or contract field when known.

The failure envelope MUST NOT coexist with a success payload, become a lifecycle finding or evidence authority, enter any fingerprint domain or authorize fallback behavior. The lifecycle alone translates it into findings and bounded evidence.

On failure:

- no mutation plan authorizing a write may be produced;
- no target write may occur;
- the refresh attempt becomes `abandoned` through the lifecycle;
- the lifecycle emits the applicable abstract finding and bounded evidence;
- no fallback renderer may be selected automatically;
- prior accepted bytes and acceptance state remain unchanged unless DPA-500 defines an explicit independent invalidation rule.

DPA-500 owns finding identifiers, severity and gate consequences.

## 15. Resource bounds and operational aborts

Renderer execution SHOULD have explicit resource controls appropriate to the target and implementation environment.

### 15.1 Semantic bounds

Contract-declared semantic bounds MAY constrain maximum input size, maximum output size, recursion depth or a deterministic step budget.

A semantic bound MUST be deterministic, documented, versioned and included in the contract fingerprint when it can affect output or validity. Exceeding it is a renderer validation or execution failure.

### 15.2 Operational safety aborts

Wall-clock timeout, host memory termination and equivalent environment-dependent safety aborts are operational controls, not semantic renderer results.

They MUST:

- terminate the attempt as `abandoned`;
- emit a lifecycle finding;
- remain outside semantic fingerprint domains;
- never produce truncated accepted output.

Retrying the identical plan is permitted.

Concrete enforcement remains `NEEDS_MAIN_REPO_VALIDATION`.

## 16. Security, isolation and capability enforcement

Registry data MUST NOT select arbitrary executable code.

Renderers MUST treat declared source text as data, not executable instructions.

Template or formatting facilities MUST NOT permit arbitrary code execution, imports, filesystem traversal or shell expansion.

Secrets, credentials and unrelated environment variables MUST NOT be exposed to renderers unless an accepted future contract explicitly establishes a bounded need. Such a future contract MUST preserve determinism and authority boundaries.

Capability enforcement has three levels:

1. **mandatory construction boundary** — the lifecycle supplies only the closed immutable invocation context from §6;
2. **mandatory conformance evidence** — deterministic negative tests cover each prohibited capability class;
3. **optional hard isolation** — process or operating-system isolation may be adopted when Probe evidence supports it.

Any detected capability violation MUST terminate the attempt as `abandoned`.

## 17. Conformance tests

A conforming implementation MUST include tests for:

1. known renderer identifier resolution;
2. unknown identifier rejection;
3. duplicate or ambiguous mapping rejection;
4. executable/dynamic registry reference rejection;
5. identical-input deterministic output;
6. fresh-process deterministic output where practical;
7. undeclared-input access rejection;
8. environment/time/randomness independence;
9. return-type enforcement;
10. renderer side-effect detection or prevention;
11. no file writes;
12. no lock acquisition;
13. no subprocess or network access;
14. no renderer chaining;
15. exactly one target per invocation;
16. payload-only region output;
17. partition-byte rejection;
18. empty-output policy;
19. malformed configuration rejection;
20. renderer semantic-version drift invalidating an existing plan;
21. prior target bytes not becoming semantic input;
22. evidence and acceptance state not becoming renderer input;
23. renderer-visible bytes matching the fingerprinted immutable source snapshot;
24. operational timeout or memory abort producing `abandoned` without semantic output;
25. bounded failure-envelope handling without a success payload or authority transfer;
26. template/import/traversal/shell-injection rejection;
27. mandatory invocation-boundary and capability-negative-test enforcement.

Tests MAY use fakes or capability-restricted contexts, but the production boundary MUST provide equivalent guarantees.

## 18. Relationship to existing command paths

Existing commands and workflows MAY request rendering only through the existing lifecycle.

They MUST NOT:

- call a renderer and write its result directly;
- bypass plan capture;
- pass ambient mutable repository objects into the renderer;
- assign acceptance based on renderer success alone.

If `CURRENT_HANDOFF.md` is later selected, the observed `admin-refresh-pr` path must route its renderer invocation through DPA-300. This statement does not select a document form and remains subject to Probe-time writer inventory and compatibility evidence.

## 19. Main-repository validation boundary

The following remain `NEEDS_MAIN_REPO_VALIDATION`:

- static renderer-map location and representation;
- callable signature and capability restriction mechanism;
- renderer interface-version and semantic-version representation;
- actual existing renderer candidates and reuse suitability;
- enforcement of filesystem, network and subprocess prohibition;
- deterministic semantic-bound and operational-abort implementation;
- integration with the observed command and lifecycle surfaces;
- finding and gate mapping;
- exact tests and CI placement.

No claim in this document states that the current main repository already conforms.

## 20. Later-spec obligations

### DPA-500

DPA-500 MUST define findings and gates for:

- unknown or changed renderer identifier;
- renderer output drift;
- nondeterministic output;
- invalid return type;
- side-effect or undeclared-input violations;
- renderer interface- or semantic-version mismatch;
- operational safety aborts and bounded renderer failure diagnostics;
- evidence and acceptance-state requirements.

### DPA-600

DPA-600 MUST ensure renderer output is never integrated from a stale base, source, contract, renderer or target context across competing refs.

### DPA-700

DPA-700 MUST define rollback consequences when renderer behavior changes or a prior renderer semantic version is no longer executable.

### DPA-800

DPA-800 MUST define:

- Probe recipes for renderer-map and purity compatibility;
- DP2 implementation steps;
- exact-ref renderer evidence;
- staged adoption and rollback;
- independent-context verification for high-risk renderer/lifecycle mutations only if later accepted governance requires it.

## 21. Invalid renderer states

The following are invalid:

1. unknown or ambiguous renderer identifier;
2. registry-selected executable import path;
3. renderer invocation before contract validation;
4. undeclared semantic input;
5. ambient repository discovery;
6. time-, random-, environment- or host-dependent semantic output not declared by contract;
7. mutable global state affecting output;
8. renderer file, state, evidence or acceptance-state write;
9. lock acquisition;
10. subprocess or network access;
11. renderer chaining;
12. multi-target output;
13. partition bytes in region payload;
14. manual or historical bytes in renderer output;
15. invalid output type;
16. disallowed empty output;
17. silent fallback renderer;
18. renderer semantic-version mismatch ignored by planning;
19. prior target or evidence used as semantic fallback;
20. renderer success represented as acceptance;
21. renderer re-opening a mutable repository path after lifecycle fingerprinting;
22. operational timeout or memory abort represented as semantic output;
23. failure diagnostics coexisting with a success payload or becoming authority;
24. template or formatting input enabling code execution, import, traversal or shell expansion;
25. capability conformance claimed without the mandatory invocation boundary and negative-test evidence.

## 22. Review-ready criteria

DPA-400 may become `review-ready` when:

1. its authority boundary is consistent with DPA-000 through DPA-300;
2. identity, input, output, purity, determinism and failure contracts are complete;
3. every requirement is traceable to invariants, decisions, tests, later gates, evidence and rollback;
4. diagrams are synchronized with the normative text;
5. repository-specific implementation statements remain exact-ref fenced;
6. primary review, secondary verification, maintainer adjudication and required post-adjudication verification are complete.

DPA-400 MUST NOT become `stable` before relevant renderer compatibility and purity Probes have evidence at an exact main-repository validation ref.
