# W0a — Website evidence integrity

Source base `fc6ae924557b68a056dab4a65618581a9d957c56`. Source hashes in inputs.json identify the primary audited inputs;
validation.json records actual tests separately.

## Scope

The three computed statuses are unchanged. Claim scopes derived from claims.yaml:
`{"documentation": 1, "historical-observation": 2, "technical": 11}`.
Technical assertions cannot verify themselves through presentation text.
Documentation assertions verify documentation only. Historical observations require
an explicit scope note: the 1.0.6 PyPI retest is not a current-installability test,
and B1 remains a historical window in one familiar repository. The four identified
claims no longer use presentation text as technical proof.

## Build integrity

The contract derives 11 direct evidence paths from current bindings
(listed in inputs.json) and checks each against the Pages manifest. Conservative
package, tools, tests and report prefixes cover transitive source changes. This can
cause additional builds; no cost reduction is claimed. A new uncovered direct input
blocks the build until its trigger is declared. The pre-install classifier continues
to use JSON and the standard library, without a YAML dependency.

Existing literal quickstart/workflow selections remain unchanged. Missing selected
names block the build; current manifest safety/surface metadata remain authoritative.
Unsupported maturity labels were removed. The strict generated docs fallback remains
byte-checked and is rebuilt from the same producer.

## Validation and remaining work

Regression injections cover circular text, historical boundaries, an uncovered new
file and a removed command. Website, Pages-policy and strict fallback tests remain
required. See validation.json for results.

W0b reselection, diagrams and K0 call-versus-recommendation edges are separate work.
Kernel keeps its architectural L0 meaning. No package release, PyPI/Zenodo publication, paid benchmark
or private consumer-source change is part of W0a.

Reproduce the website with site/scripts/build.py; inspect scopes in claims/claims.json
and inputs through direct_evidence_paths in site_evidence_contract.py. This report
is explanatory evidence, never evidence for its own website claims.
