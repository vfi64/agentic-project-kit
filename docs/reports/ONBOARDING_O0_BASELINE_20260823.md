# Onboarding O0 Baseline

Status: completed read-only baseline  
Date: 2026-08-23  
Repository: vfi64/agentic-project-kit  
Branch: codex/onboarding-o0-baseline  
Base main: a35be312

## Purpose

This report records the O0 baseline for `measured-agent-onboarding` in
`docs/planning/PROJECT_DIRECTION.yaml`.

O0 is intentionally read-only. It measures the current first-contact surfaces
and records the smallest follow-up requirements for O1/O2. It does not add new
onboarding guidance, change command behavior, alter workspace detection, or
create a second planner/workflow authority.

## Measurement Boundary

This is a repository-observed baseline, not a blind fresh-agent transcript. The
current Codex environment can inspect the repository directly, but this slice did
not spawn a separate independent task merely to simulate a new user. That keeps
the evidence honest: O0 measures the visible source surfaces and their current
friction points, while O4 should make this repeatable as a deterministic
measurement contract.

## Source Surfaces Inspected

- `README.md`
- `docs/guides/BROWNFIELD_EXTERNAL_REPO_15_MINUTES.md`
- `docs/reference/agentic-kit-commands.json`
- `src/agentic_project_kit/workspace_detection.py`
- `src/agentic_project_kit/checks.py`
- `src/agentic_project_kit/doctor.py`

## Observed Baseline

| Signal | Observation |
|---|---|
| Dedicated onboarding document | `docs/ONBOARDING.md` is absent. |
| README size | `README.md` has 751 lines. |
| Brownfield guide size | `docs/guides/BROWNFIELD_EXTERNAL_REPO_15_MINUTES.md` has 148 lines. |
| README first concrete generated-project path | The Quick start section begins at line 96; concrete `agentic-kit init` examples appear at lines 142 and 148. |
| README existing-repo path | `Govern an existing repository (operating layer)` starts at line 263. |
| README command-density proxy | 138 lines match command-like tokens across the full README. |
| README Quick start command-density proxy | 7 command-like lines appear in lines 96-169. |
| README existing-repo command-density proxy | 16 command-like lines appear in lines 263-327. |
| Brownfield guide command-density proxy | 21 command-like lines appear across the guide. |
| README advanced-topic proxy | 43 lines mention DPA, GUI, release, DOI, Zenodo, Cockpit, Workflow Output Cycle, or Pattern Advisor. |
| Canonical non-workspace message | `workspace_detection.non_workspace_message()` tells users to run `agentic-kit init NAME` for a governed project or `agentic-kit workspace init --root PATH` for an existing repository. |
| Shared non-workspace message usage | `checks.py` and `doctor.py` call the canonical helper instead of duplicating the text. |
| Command manifest availability | The manifest contains `agentic-kit init`, `agentic-kit workspace init`, `agentic-kit doctor`, `agentic-kit check`, `agentic-kit workflow state`, and `agentic-kit command-for`. |

The command-density proxy counted lines containing one of: `agentic-kit `,
`python -m `, `ruff `, `pytest `, or `git `.

## Friction Points

1. There is no single canonical onboarding entry point that helps a first-chat
   user choose between creating a new governed project, adopting an existing
   repository, and developing the Kit itself.
2. The README contains the needed information, but first-contact routes are
   separated by many sections and mixed with release, GUI, DOI, DPA, workflow,
   and governance details.
3. The brownfield guide is a useful shortest existing-repo path, but it is not a
   general first-chat orientation document and still assumes the reader already
   knows they want the operating-layer path.
4. Workspace detection already has the right canonical next-step wording. Future
   onboarding should bind to that source rather than copying unmanaged command
   strings into multiple documents.

## O1/O2 Requirements

O1 should add a minimal `docs/ONBOARDING.md` and a small README anchor. The new
document should have exactly one decision point for the first route:

- create a new governed project;
- add the Kit operating layer to an existing repository;
- work on the Kit repository itself.

O2 should add drift protection by binding onboarding references to the generated
command manifest and the canonical workspace-detection message source. It should
not duplicate command help or introduce a parallel planning surface.

## Evidence

- Current command manifest ACK: `COMMAND_MANIFEST_ACK a6c875ef652f`
- O0 branch start: `a35be312`
- Repo status before edits: clean
- Carrier task id: `14c20cbbb6de3006`
- Verified task body SHA-256:
  `73469189b052e196728d766bc175968e1588c7c43c51c19efd30953905c51981`
