# DPA-ADR-019 — Renderer Input, Resource and Version Model

Status: ACCEPTED
Date: 2026-07-16

## Context

The DPA-400 primary review found three contract ambiguities:

1. a renderer was permitted to read declared sources while the invocation context was also required to be immutable and sufficient without ambient repository reads;
2. deterministic semantic resource limits were conflated with host-dependent operational aborts;
3. renderer identifier, renderer contract version, renderer-version identity and implementation commit evidence were not related by one closed vocabulary.

These defects affect determinism, plan identity, acceptance-state comparison and DPA-500 findings.

## Decision

### 1. Renderer-visible source identity

A renderer MUST consume only lifecycle-resolved immutable source values or immutable content-addressed snapshots.

A renderer MUST NOT open, re-read, re-resolve, glob, traverse or search mutable repository paths.

If a bounded path-like handle is required for a large source, the lifecycle MUST guarantee that:

- the referenced bytes are immutable for the invocation;
- the fingerprinted bytes and renderer-visible bytes are the same content-addressed object;
- the renderer cannot use the handle to discover adjacent repository content.

### 2. Resource-policy split

Renderer resource policy has two distinct classes.

**Semantic bounds** are deterministic, contract-declared and versioned constraints such as maximum input size, maximum output size, recursion depth or deterministic step budget. They are fingerprint-relevant when output-affecting.

**Operational safety aborts** are host-dependent protections such as wall-clock timeout or process memory termination. They:

- terminate the refresh attempt as `abandoned` through the lifecycle;
- MUST NOT become semantic renderer output;
- MUST NOT enter renderer, contract, plan or acceptance-state fingerprint domains;
- MUST NOT authorize truncated output;
- MAY permit retry of the same still-valid plan.

### 3. Renderer identity and version vocabulary

The renderer model has exactly four distinct concepts:

- **renderer identifier** — the stable declarative key used by the closed static renderer map;
- **renderer interface version** — the version of the lifecycle-to-renderer callable and value-object contract;
- **renderer semantic version** — the version that changes whenever implementation behavior may change output for identical governed inputs;
- **renderer implementation evidence** — commit SHA, file hash or equivalent reproducibility evidence; evidence-only and not automatically fingerprint-relevant.

The renderer semantic version is the renderer-version token captured by projection contracts, mutation plans, acceptance-state records and output-related evidence.

A repository commit SHA MUST NOT substitute for renderer semantic version, because unrelated repository changes MUST NOT invalidate all renderer plans.

## Alternatives considered

1. Let renderers reopen validated repository paths — rejected because fingerprinted and consumed bytes may diverge.
2. Treat wall-clock timeouts as deterministic contract bounds — rejected as unsatisfiable and semantically incorrect.
3. Use one generic `renderer version` token for interface, semantics and implementation evidence — rejected because incompatible changes and output changes have different consequences.
4. Use current repository HEAD as renderer version — rejected because unrelated commits would cause false invalidation.

## Rationale

Determinism requires fixed renderer-visible inputs. Resource safety requires operational aborts without making host conditions semantic inputs. Plans and drift classification require one unambiguous output-relevant renderer version while preserving interface compatibility and evidence separately.

## Consequences

- DPA-100 MUST register the four renderer identity/version terms.
- DPA-300 MUST replace `renderer contract version` with `renderer semantic version` where output identity is intended and MUST add `renderer interface version` where callable compatibility is required.
- DPA-400 MUST apply immutable input/snapshot semantics, the resource split and the four-part version model.
- DPA-500 MUST distinguish semantic-bound failure from operational abort findings.
- DPA-700 MUST define rollback when a required renderer semantic version is unavailable.
- DPA-800 MUST define concrete representation and Probe recipes.

## Validation status

NORMATIVE architecture decision. Concrete snapshot mechanism, renderer map, interface representation and operational enforcement remain `NEEDS_MAIN_REPO_VALIDATION`.

## Affected specifications

DPA-100, DPA-300, DPA-400, DPA-500, DPA-700 and DPA-800.

## Affected DP slices

DP1–DP5.