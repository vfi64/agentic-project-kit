# Project Direction

Status: active
Decision status: accepted
Review policy: required

- Strategic direction updated after PR: `2591`
- Authority: `docs/planning/PROJECT_DIRECTION.yaml`

`docs/planning/PROJECT_DIRECTION.yaml` is the canonical machine-readable source. This generated view is not independent planning authority.

## Plans

- `master-implementation-q` - **Master Implementation Q2 rest sequence** (`done`)
  Historical ordering authority for the Q2 rest sequence after PR1806: CM3/CM4, LC/ID/K3, P5b/P5d/P5c-PLAN/P6, LC3/TH1, and L. A0 reconciliation after v1.0.4 keeps the historical evidence but removes this item as an active planning driver because the listed sequence is either done or maintainer-gated, and current work is now represented in the canonical Direction records.
- `command-manifest-hardening` - **Command manifest hardening** (`done`)
  Make the generated command manifest hash-addressable, safety-annotated, and gate-checked before selector and lint work depend on it.
- `command-for-selector` - **Deterministic command selector** (`done`)
  Use the hardened manifest to map raw command requests to approved wrappers deterministically.
- `instruction-lint-gate` - **Instruction lint gate** (`done`)
  Reject unsafe or stale instruction payloads before transfer apply can execute them. Engine and GUI lint integration shipped in PR #1811, direction closeout in PR #1813, transfer apply gating in PR #1817, and apply-gate test closure in PR #1819.
- `chat-entrypoint-contract` - **Chat entrypoint manifest contract** (`done`)
  Keep AGENTS, initial prompts, refresher output, and carrier headers pinned to the current command manifest.
- `lock-contract-audit` - **Audit workspace mutation-lock coverage** (`done`)
  Captured the current mutation-lock coverage and gap list in PR #1821 before LC2 decides the reentrancy and wrapper-boundary policy.
- `lock-reentrancy-decision` - **Decide mutation-lock reentrancy and inherited-lock policy** (`done`)
  Selected same-PID reentrancy in PR #1823 as the durable lock policy so protected primitives can remain safe when called directly or by higher-level orchestrators.
- `lock-coverage-remediation` - **Remediate mutation-lock coverage gaps** (`done`)
  PR #1843 applies the LC2 same-PID-reentrant lock decision to runtime mutators, promotes the mutation-lock audit into the standard suite, and keeps false-positive-prone findings visible but non-blocking.
- `negative-path-hardening` - **Harden Q2 TH1 negative paths** (`done`)
  PR #1845 captures missing-source, malformed-input, and collision failure paths with deterministic tmp_path tests, then hardens only unclear or unstructured failure output.
- `doc-lifecycle-metadata` - **Add documentation lifecycle metadata and report-only consistency gate** (`done`)
  PR #1849 makes registry-backed lifecycle metadata explicit before lifecycle signals or sweep automation depend on it, extending the existing lifecycle audit with report-only JSON findings rather than adding a duplicate audit path.
- `doc-lifecycle-signals` - **Add documentation lifecycle obsolescence signals** (`done`)
  PR #1852 turns review-after values, Direction coupling, and orphan indicators into report-only lifecycle findings so L3 can sweep visible signals without weakening existing gates.
- `doc-lifecycle-sweep` - **Add guided documentation lifecycle sweep workflows** (`done`)
  PR #1854 uses lifecycle findings to produce bounded archive, confirm-current, defer, bootstrap, and GUI dry-run actions without destructive defaults.
- `doc-lifecycle-strict-adoption` - **Adopt documentation lifecycle enforcement gradually** (`done`)
  PR #1857 promotes lifecycle audit coverage through WARN and strict modes without making current kit cleanup a hidden prerequisite. The current kit repository still carries visible lifecycle hygiene findings, so strict standard-suite adoption remains gated by lifecycle-backlog-clearance.
- `lifecycle-backlog-clearance` - **Clear current documentation lifecycle backlog before suite-level strict mode** (`active`)
  The L4 strict switch exists, but the current repository is intentionally not strict-clean yet. Keep the standard gate suite in visible WARN mode until a documented sweep clears or defers existing lifecycle findings.
- `hygiene-manifest-adopt-baseline` - **Add manifest hygiene and adopt baseline lifecycle support** (`done`)
  PR #1860 connects lifecycle hygiene to workspace manifests, init seeds, and adopt baselines after strict adoption is staged. The current kit manifest intentionally keeps using default hygiene settings until a later explicit strict-cleanup decision.
- `repo-identity-literals` - **Derive repository identity literals from workspace context** (`done`)
  Replaced successor handoff self-hosting identity literals with git-origin repository identity derivation in PR #1825 before path and identity literal enforcement tightens.
- `repo-identity-sweep` - **Classify remaining repository identity literals** (`done`)
  PR #1827 classified remaining source-level repository identity literals into active, reference, template, and declared-exception groups; active identity literal modules are zero before active identity-literal enforcement tightens in P5b.
- `direction-schema-command-migration` - **Introduce direction schema, command, migration, cleanup, scope, and gate slices** (`done`)
- `governance-doc-backfill` - **Backfill reviewed governance document registry entries** (`active`)
- `strict-scope-suite-adoption` - **Decide whether strict documentation scope belongs in the standard gate suite** (`done`)
- `planning-ideas-residual-cleanup` - **Resolve remaining planning and idea residual documents** (`planned`)
- `pre-gui-hardening-plan` - **Execute the pre-GUI hardening backlog in small wrapper-first slices** (`active`)
- `decomplexification-audit-roadmap` - **Reduce command-surface complexity through compatibility-preserving facades** (`active`)
- `context-budgeted-handoff-projections` - **Reduce agent token consumption through deterministic context projections** (`planned`)
  Long-running agentic work now carries substantial repo-backed state, evidence, reports, and handoff projections. The reduction target is not less governance but smaller task-specific context packets rendered from the same deterministic repository authorities.
- `kit-control-effectiveness-measurement` - **Measure the effectiveness and cost of the Kit's own control mechanisms** (`planned`)
  The Kit enforces correct agent behaviour through many commands, gates and projections, but cannot yet show which of them are used, which prevent drift and what they cost. The October 2026 audits found 25 of 266 public commands with no execution evidence, no persistent invocation record, a documented direct-Git bypass (F4), a stale secondary handoff projection (HD-08, fixed by PR 2510) and administrative refresh PRs at 50 % of October PRs and 22 % of PR-head CI time. The next step is measurement before further rules or command removal, extending existing mechanisms instead of adding a new planning or research system.
- `website-evidence-and-command-navigation` - **Improve the public website with gated quickstart, evidence and governed command navigation** (`done`)
  The site presents a large command surface as filtered tables. It needs a short verifiable start path and bounded safety evidence without freezing commands that decomplexification may consolidate. At 83977b75 there are 268 commands including 34 orchestrators; all orchestrators have structural task_tags but only two have additional task-specific tags, and the site generator does not currently project task_tags. Decomplexification has no fixed completion date.
- `independent-held-out-gate-validation` - **Test known Kit gate claims against independently developed held-out faults** (`planned`)
  The existing 11/11 offline benchmark targets known faults and is partly fix-informed. Independently developed unseen scenarios can challenge its generalization and methodology without implying universal security.
- `optional-structural-evidence-provider-evaluation` - **Evaluate optional structural evidence providers for impact-aware context** (`planned`)
  Local code graphs may reduce repeated file-reading and improve impact-scope selection, but they must remain evidence inputs rather than a second governance authority. Graphify is the first candidate because its public materials describe local deterministic Tree-sitter parsing and file-based graph artifacts.
- `next-turn-workflow-kernel` - **Move recurring next-step execution from chat discipline into a deterministic local workflow kernel** (`active`)
- `release-command-authority` - **Keep release preparation, publishing, and DOI closeout under explicit command authority** (`active`)
- `rule-registry-hardening` - **Preserve active rule identity, source validation, and refresh handshakes** (`active`)
- `portability-and-ns-closeout` - **Finish replacing legacy ns adapter dependencies with Python-backed agentic-kit commands** (`done`)
- `gui-workbench-plan` - **Implement the GUI gatekeeper/workbench as a view over governed action specs** (`planned`)
- `docs-centralize-and-remove-command` - **Build governed docs centralize-and-remove command before K3** (`planned`)
- `standard-error-hardening-backlog` - **Standard-error hardening backlog and legacy ns command coverage map** (`active`)
- `post-merge-lifecycle-state-model` - **Post-merge lifecycle state model and command authority** (`active`)
- `post-v1-0-4-hygiene-boundary-work-program` - **Post-v1.0.4 hygiene, boundary, and open-question work program** (`active`)
- `obsolete-pr660-handoff-overlay` - **Obsolete PR660 handoff overlay centralized** (`done`)
- `release-command-authority-slice` - **Release command authority slice centralized** (`done`)
- `mechanize-doc-registry-scope-reconcile` - **Mechanize documentation registry scope reconciliation** (`planned`)
  K2b exposed existing renderer/test logic for documentation registry scope decisions, but no exposed agentic-kit command wraps refresh, stale-projection detection, registry consistency, coverage, and diagnostics as a deterministic transaction.
- `mechanize-failure-mode-review-automation` - **Mechanize failure-mode review automation** (`planned`)
  The archived plan identified repeated workflow failures that must become repository-backed commands, tests, and gates rather than chat-only prompts.
- `mechanize-pre-gui-hardening-readiness` - **Mechanize pre-GUI hardening readiness** (`planned`)
  The archived pre-GUI plan collected post-v0.4.11 hardening tasks that should be expressed as commands, gates, status reports, or cockpit metadata before GUI expansion.
- `mechanize-operating-layer-public-onboarding-evidence` - **Mechanize operating-layer public onboarding and evidence** (`planned`)
  The archived masterplan still contains useful residual follow-up beyond the accepted architecture, especially public documentation, website framing, installation versus repository onboarding, evidence logs for current-state claims, and external-repo validation.
- `reports-retention-policy` - **Mechanize report and evidence retention policy** (`planned`)
- `agf-dpa-adoption-tracker` - **Track AGF/DPA Package-G adoption evaluation without implementation claims** (`blocked`)
  The Kit must not silently adopt AGF, DPA or ROS artifacts from external repositories, draft PRs or chat context. A repository-local tracker keeps the obligation visible while preserving Kit authority over its planning, runtime, gates, registries, lifecycle, handoff state and implementation evidence.
- `external-rule-registry-bootstrap-adjudication` - **Adjudicate external rule-registry bootstrap and gate applicability** (`planned`)
- `dpa-current-evidence-continuity` - **Restore verifiable DPA evidence continuity for current strict and stable checks** (`done`)
  Current targeted checks block on missing historical adjudication evidence despite recorded historical stable promotion.
- `proof-assurance-assessment` - **PAA — Proof Assurance Assessment: investigation and development plan for trustworthy software evidence** (`planned`)
  Assess an optional profile-bound verification domain within existing Kit authority. Prevent unsupported correctness claims; establish usefulness and implementation reuse before development.
- `guided-gui-alternative` - **Validate an optional guided Kit GUI over shared guarded actions** (`active`)
- `external-retest-machine-contracts` - **Give every local finding retest a machine contract and resync the external ledger** (`active`)
  At the historical 1.1.4 baseline KIT-GF-070 was PARTIAL; the Cockpit retest returned PASS 8, FAIL 0, NO_MACHINE_CONTRACT 34, NOT_RUN_LOCALLY 37, and 16 consumer families were OPEN against a Kit closure. The step evidence below supersedes those baseline counts. Kit closure and released-consumer VERIFIED_FIXED remain separate decisions.
