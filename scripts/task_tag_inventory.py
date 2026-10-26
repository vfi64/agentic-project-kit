"""W1-P0 metadata inventory, not a preferred-command or authorization authority.

Developer-only reproducible report. No Kit workflow or model calls are executed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import subprocess

from agentic_project_kit.command_manifest import _task_tags
from agentic_project_kit.command_selector import select_for_task

MANIFEST = "docs/reference/agentic-kit-commands.json"
PRODUCER = "src/agentic_project_kit/command_manifest.py"
SELECTOR = "src/agentic_project_kit/command_selector.py"
HISTORICAL = "83977b75"


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout


def inventory(manifest: dict) -> dict:
    commands = manifest["commands"]
    names = [c["qualified_name"] for c in commands]
    if any(not isinstance(n, str) or not n.strip() for n in names) or len(names) != len(set(names)):
        raise ValueError("invalid or duplicate command identity")
    for command in commands:
        tags = command.get("task_tags", [])
        if not isinstance(tags, list) or any(not isinstance(t, str) or not t.strip() for t in tags):
            raise ValueError("invalid task tags")
    rows = []
    by_tag: dict[str, list[str]] = defaultdict(list)
    by_set: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for command in sorted(commands, key=lambda c: c["qualified_name"]):
        if command.get("surface") != "orchestrator":
            continue
        name = command["qualified_name"]
        actual = sorted(set(command.get("task_tags", [])))
        # Reuse the producer with no command identity: only its group/safety
        # derivation remains, without the command-specific EXTRA_TASK_TAGS map.
        structural = set(_task_tags({**command, "qualified_name": ""}))
        additional = sorted(set(actual) - structural)
        rows.append({"command": name, "group": command["group"], "safety": command["safety"],
                     "tags": actual, "structural_tags": sorted(set(actual) & structural),
                     "missing_structural_tags": sorted(structural - set(actual)),
                     "additional_tag_candidates": additional,
                     "assignment": "candidate_tags_present" if additional else "unassigned",
                     "producer_default_matches": set(_task_tags(command)) == set(actual),
                     "when_to_use": command.get("when_to_use", "")})
        for tag in actual:
            by_tag[tag].append(name)
        if actual:
            by_set[tuple(actual)].append(name)
    selections = []
    for tag, owners in sorted(by_tag.items()):
        selected = select_for_task(manifest, tag)
        if selected.status != "match":
            raise ValueError("selector does not resolve a declared tag")
        matches = [c["qualified_name"] for c in selected.payload["commands"]]
        selections.append({"tag": tag, "orchestrators": owners,
                           "selector_matches_all_surfaces": matches,
                           "multiple_orchestrators": len(owners) > 1,
                           "semantic_ambiguity": "NOT_ASSESSED"})
    unassigned = [r["command"] for r in rows if not r["additional_tag_candidates"]]
    return {"counts": {"orchestrators": len(rows), "with_any_tags": sum(bool(r["tags"]) for r in rows),
                       "with_additional_tag_candidates": sum(bool(r["additional_tag_candidates"]) for r in rows),
                       "unassigned": len(unassigned),
                       "multi_orchestrator_tags": sum(r["multiple_orchestrators"] for r in selections)},
            "orchestrators": rows, "unassigned": unassigned, "tag_selections": selections,
            "identical_tag_sets": [{"tags": list(tags), "commands": owners}
                                   for tags, owners in sorted(by_set.items()) if len(owners) > 1]}


def generate(root: Path, source_commit: str) -> dict:
    source = git(root, "rev-parse", "--verify", "--end-of-options", source_commit + "^{commit}").strip()
    hashes = {}
    for path in (MANIFEST, PRODUCER, SELECTOR):
        committed = git(root, "show", f"{source}:{path}").encode()
        if committed != (root / path).read_bytes():
            raise ValueError(f"input differs from pinned source: {path}")
        hashes[path] = hashlib.sha256(committed).hexdigest()
    current_manifest = json.loads((root / MANIFEST).read_text())
    current = inventory(current_manifest)
    historical_commit = git(root, "rev-parse", "--verify", "--end-of-options", HISTORICAL + "^{commit}").strip()
    historical = inventory(json.loads(git(root, "show", f"{historical_commit}:{MANIFEST}")))
    return {"schema_version": 1, "kind": "task_tag_metadata_inventory",
            "artifact_type": "evidence", "status": "active", "review_policy": "historical_evidence",
            "analysis_status": "COMPLETE_METADATA_INVENTORY", "semantic_coverage": "NOT_ASSESSED",
            "source_commit": source, "manifest_sha": current_manifest["meta"]["manifest_sha"],
            "input_sha256": hashes,
            "generator": {"path": "scripts/task_tag_inventory.py",
                          "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
            "historical_baseline": {"source_commit": historical_commit, "counts": historical["counts"],
                                    "method": "Same metadata lens on the committed historical manifest; no historical runtime execution."},
            **current,
            "limits": ["Any-tag coverage is not semantic task coverage.",
                       "Additional tags are candidates, not evidence of meaningful or complete task mapping.",
                       "Multi-match tags and identical tag sets are review inputs, not proven semantic conflicts.",
                       "Selector order is its current deterministic order, not a new preferred-route decision.",
                       "No authorization, workflow-state suitability, invocation frequency or context-token reduction is measured.",
                       "Manifest and selector are unchanged; D1 owns a later shared task authority."]}


def render(report: dict) -> str:
    counts, old = report["counts"], report["historical_baseline"]
    lines = ["# W1-P0 — Task-tag metadata inventory", "",
             f"Source: `{report['source_commit']}`; manifest `{report['manifest_sha']}`.",
             f"Analysis: `{report['analysis_status']}`. Semantic coverage: `{report['semantic_coverage']}`.",
             f"Generator: `{report['generator']['path']}`; SHA-256 `{report['generator']['sha256']}`.", "",
             "## Counts and historical comparison", "",
             "| Snapshot | Orchestrators | Any tags | Additional tag candidates | Unassigned |",
             "|---|---:|---:|---:|---:|"]
    for label, c in ((old["source_commit"], old["counts"]), (report["source_commit"], counts)):
        lines.append(f"| `{label}` | {c['orchestrators']} | {c['with_any_tags']} | {c['with_additional_tag_candidates']} | {c['unassigned']} |")
    lines += ["", old["method"], "", "## Every current orchestrator", "",
              "Structural means the existing producer's group and safety tags. Additional tags only identify review candidates.", "",
              "| Command | Structural tags present | Additional candidates | Missing structural tags | Assignment |",
              "|---|---|---|---|---|"]
    for r in report["orchestrators"]:
        lines.append("| " + " | ".join([f"`{r['command']}`", ", ".join(r["structural_tags"]) or "none",
                    ", ".join(r["additional_tag_candidates"]) or "none",
                    ", ".join(r["missing_structural_tags"]) or "none", r["assignment"]]) + " |")
    lines += ["", "## Additional candidates and declared command intent", "",
              "The descriptions below come from when_to_use; their semantic adequacy still needs D1 review.", "",
              "| Command | Additional candidates | Manifest intent |", "|---|---|---|"]
    for r in report["orchestrators"]:
        if r["additional_tag_candidates"]:
            lines.append("| " + " | ".join([f"`{r['command']}`", ", ".join(r["additional_tag_candidates"]),
                                            r["when_to_use"].replace("|", "\\|")]) + " |")
    lines += ["", "## Explicitly unassigned", "",
              "No additional task tags were found for these commands; no task is guessed from the command name.", ""]
    lines += [f"- `{name}`" for name in report["unassigned"]] or ["None."]
    lines += ["", "## Multi-match tags (semantic ambiguity not assessed)", ""]
    for r in report["tag_selections"]:
        if r["multiple_orchestrators"]:
            lines += [f"### `{r['tag']}`", "", "Orchestrators: " + ", ".join(f"`{n}`" for n in r["orchestrators"]),
                      "", "Actual command-for matches, all surfaces, in selector order: " + ", ".join(f"`{n}`" for n in r["selector_matches_all_surfaces"]), ""]
    lines += ["## Identical tag-set candidates", ""]
    for r in report["identical_tag_sets"]:
        lines.append("- " + ", ".join(r["tags"]) + ": " + ", ".join(f"`{n}`" for n in r["commands"]))
    lines += ["", "## D1 and agent-context follow-up", "",
              "Use the listed missing assignments and collisions as input to the existing decomplexification and context-budget plans. D1 must review task intent, diagnostics versus mutations, compatibility and state/permission conditions before choosing shared preferred routes. Do not infer token savings, authorization or semantic coverage from these counts.", "",
              "## Limits", ""] + ["- " + item for item in report["limits"]]
    lines += ["", "## Reproduction", "",
              "Run the developer script scripts/task_tag_inventory.py with --source-commit set to the pinned source above and --out set to an output directory. Both source commits must exist locally; this developer tool does not fetch missing history. It only reads Git/manifest data and writes inventory.json and README.md; it does not execute Kit commands or model runs. Tests are reported separately, never fabricated as part of metadata generation."]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    report = generate(root, args.source_commit)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "inventory.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    (args.out / "README.md").write_text(render(report))
    print(json.dumps({"analysis_status": report["analysis_status"], "counts": report["counts"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
