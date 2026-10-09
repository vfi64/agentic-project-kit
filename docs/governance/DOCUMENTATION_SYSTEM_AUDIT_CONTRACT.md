# Documentation System Audit Contract

Status: active governance contract

`agentic-kit docs-audit` is the umbrella documentation-system audit. It reports these dimensions in order:

1. Aktualität
2. Vollständigkeit
3. Korrektheit
4. Redundanzfreiheit
5. Stringenz der Dokumentenordnung
6. Dokumentationsregistry
7. Konsistenz

The command aggregates deterministic findings from existing documentation checks and names review-only boundaries where full semantic proof is not possible. Document word budgets are configured in `sentinel.yaml`: `max_words` remains the hard fail-closed limit, while optional `warn_words` creates a non-blocking headroom warning so current information can be preserved while maintainers move durable history into archive or evidence documents.

Required command:

```bash
agentic-kit docs-audit
```

Optional report:

```bash
agentic-kit docs-audit --report docs-audit.json
```

Successor chats must preserve this source order:

1. `.agentic/compiled_agent_context.yaml`
2. `docs/governance/FINAL_SUMMARY_CONTRACT.md`
3. `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`
4. `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`
5. `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`
6. `docs/TEST_GATES.md`
7. `docs/STATUS.md`
8. `docs/handoff/CURRENT_HANDOFF.md`

## External manifest workspaces (KIT-GF-035)

The fixed source order and Kit document set above apply to Kit self-hosting.
For external manifest workspaces the same seven dimensions use these declared
contracts instead:

- Required documents, sections and word budgets come from `sentinel.yaml` and
  `docs/DOC_REGISTRY_SCOPE.yaml`; an existing documentation coverage matrix is
  also checked. Missing declared files and malformed declarations still block.
  Markdown files inside the declared registry scope must be registered, with
  the scope's existing exemptions respected.
- The version mesh uses the workspace's own project version and
  `release.version_anchors`, including optional literal package versions,
  changelog, citation and current-state anchors. A repository without a literal
  project version has no applicable version mesh.
- The registry is resolved through workspace paths, normally
  `.agentic/registries/documentation.yaml`. An existing legacy registry remains
  supported when that path is absent. Empty bootstrap registries are valid.
  Entries retain path/class/owner requirements, uniqueness, file existence and
  DPA contracts. Standard classes and workspace-declared `class_rules` are
  accepted; the complete Kit class-rule inventory is not required. Registered
  canonical facts retain blocking managed projections and advisory review paths.
- Successor handoff contracts apply only with the transfer module enabled.
  An absent previous handoff is a legitimate fresh state. Existing handoff state
  and successor packages are validated with the existing contract validators;
  an existing package must contain all five canonical files;
  stored validation status alone is not trusted. The Kit's fixed source order is
  never imposed on the workspace.
- `hygiene.doc_lifecycle: warn` makes lifecycle findings non-blocking warnings in
  both audits. `strict` retains blockers; explicit `doc-lifecycle-audit --strict`
  overrides warn mode. `off` suppresses lifecycle findings. These modes do not
  suppress required-file, version, registry or handoff integrity failures.

`agentic-kit docs-audit --json` prints exactly one JSON document containing
`result_status`, `scope`, dimensions, blockers as findings and warnings. Exit 0
means PASS; exit 1 means a blocking audit finding. The command is read-only with
no remote effects; `--report` writes only the requested local report.

Release metadata authority evidence is discovered under the workspace's resolved
tmp and reports roots, including `.agentic/state/handoff/reports/release/`.
Existing evidence content and version/changed-path authority checks remain
mandatory; discovering a file does not by itself authorize metadata changes.
