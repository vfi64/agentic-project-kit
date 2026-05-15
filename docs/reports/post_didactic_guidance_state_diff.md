diff --git a/docs/STATUS.md b/docs/STATUS.md
index f048f7a..38f88c0 100644
--- a/docs/STATUS.md
+++ b/docs/STATUS.md
@@ -61,6 +61,7 @@ The latest verified gates before v0.3.7 release preparation were:
 - PR #170 added read-only `agentic-kit workflow status --explain`, documented it, and raised the suite to 160 tests.
 - PR #171 refreshed current-state and handoff documentation after PR #170.
 - PR #172 completed Guided Workflow Usability v1 and raised the suite to 162 tests.
+- PR #195 added `docs/ideas/DIDACTIC_GUIDANCE.md` as a documentation-only, non-binding didactic orientation note and cross-linked it from state, handoff, and agent guidance docs.
 
 ## Idea-note state
 
@@ -70,6 +71,7 @@ The repository has four related non-binding architecture idea notes:
 - `docs/ideas/DETERMINISTIC_CELL_ORCHESTRATION.md`
 - `docs/ideas/LAYERED_CLI_USABILITY.md`
 - `docs/ideas/PATTERN_ADVISOR.md`
+- `docs/ideas/DIDACTIC_GUIDANCE.md`
 
 These documents preserve architecture options without making them automatic implementation requirements.
 
@@ -213,12 +215,12 @@ Project-level state documentation is machine-checkable:
 
 ## Current Goal
 
-v0.3.9 is released and post-release verified. GitHub Release exists, and Zenodo verified version DOI is `10.5281/zenodo.20210345`.
+v0.3.9 is released and post-release verified. GitHub Release exists, Zenodo verified version DOI is `10.5281/zenodo.20210345`, and PR #195 has added the didactic guidance foundation note on main.
 
 ## Current Blockers
 
-- Local gates must pass on `docs/record-v0.3.7-doi`.
-- Release metadata, package version, citation metadata, changelog, status, and handoff must agree before tagging.
+- No current blockers are known after PR #195.
+- Next work should start from a new narrow slice with an explicit command-level contract.
 
 ## Live Status Commands
 
diff --git a/docs/handoff/CURRENT_HANDOFF.md b/docs/handoff/CURRENT_HANDOFF.md
index aa1e3cc..6e4529a 100644
--- a/docs/handoff/CURRENT_HANDOFF.md
+++ b/docs/handoff/CURRENT_HANDOFF.md
@@ -9,46 +9,35 @@ Base branch: main
 
 ## Current Goal
 
-v0.3.9 is released and post-release verified. GitHub Release exists, and Zenodo verified version DOI is `10.5281/zenodo.20210345`.
-
-v0.3.7 is complete. The v0.3.8 planning note is merged on main, and the first narrowly scoped Guided CLI Usability v2 slice is merged on main.
+v0.3.9 is released and post-release verified. GitHub Release exists, Zenodo verified version DOI is `10.5281/zenodo.20210345`, and PR #195 has added the didactic guidance foundation note on main.
 
 ## Current Repository State
 
-v0.3.7 is released and post-release verified. Verified v0.3.7 version DOI: `10.5281/zenodo.20206581`. The post-release Zenodo verification is complete for v0.3.7.
-
-Verified release evidence:
-
-- GitHub Release v0.3.7 exists.
-- Zenodo concept DOI: `10.5281/zenodo.20101359`.
-- Verified v0.3.7 version DOI: `10.5281/zenodo.20206581`.
-- `agentic-kit post-release-check --version 0.3.7` passed.
-- PR #163 recorded the verified v0.3.6 DOI metadata on main.
-
-Post-release work completed after v0.3.6:
-
-- PR #164 preserved `docs/ideas/DETERMINISTIC_CELL_ORCHESTRATION.md` as a curated idea note.
-- PR #164 introduced `docs/ideas/LAYERED_CLI_USABILITY.md` as a non-binding usability-layer model.
-- PR #164 added small `AGENTS.md` cross-references to the DCO and layered CLI usability idea notes.
-- PR #165 refreshed `docs/STATUS.md` and `docs/handoff/CURRENT_HANDOFF.md` after the idea-note merge.
-- PR #166 hardened `agentic-kit workflow cleanup` so stale `temp/workflow-evidence-*` branches can be removed even when `.agentic/workflow_state` is already `IDLE`.
-- PR #167 refreshed `docs/STATUS.md` and `docs/handoff/CURRENT_HANDOFF.md` after workflow cleanup hardening.
-- PR #168 added `docs/ideas/PATTERN_ADVISOR.md` as a non-binding idea note / architecture research track.
-- PR #170 added read-only `agentic-kit workflow status --explain` guidance for common workflow states.
-- PR #171 refreshed `docs/STATUS.md` and `docs/handoff/CURRENT_HANDOFF.md` after PR #170.
-- PR #172 completed Guided Workflow Usability v1 with read-only safety wording, `current_report` explanation, a README quick command guide, and a guided status compass.
-
-The v0.3.7 release-preparation PR was merged on main after:
+Current main head after PR #195:
 
 ```text
-0161838 Complete guided workflow status usability (#172)
-a2d5e68 Update status and handoff after workflow status explain (#171)
-1d0c5f4 Explain workflow status next steps (#170)
+401e98d Add didactic guidance foundation note (#195)
+d877802 Finalize post-v0.3.9 DOI state (#194)
+fa386b6 Record v0.3.9 DOI metadata (#193)
+bb15d82 tag: v0.3.9, Finalize pre-v0.3.9 release state (#192)
+ef72e37 Prepare v0.3.9 release metadata (#191)
+239047d Finalize post-repo-ns-entrypoint state (#190)
+68614a3 Add repo ns compatibility entrypoint (#189)
+7660db5 Finalize post-failed-status-guidance state (#188)
 ```
 
-Latest verified local gates after v0.3.7 release preparation:
+Verified release and post-merge evidence:
+
+- GitHub Release v0.3.9 exists.
+- Zenodo concept DOI: `10.5281/zenodo.20101359`.
+- Verified v0.3.9 version DOI: `10.5281/zenodo.20210345`.
+- `agentic-kit post-release-check --version 0.3.9` passed before PR #195.
+- PR #195 added `docs/ideas/DIDACTIC_GUIDANCE.md` as a documentation-only, non-binding didactic orientation note.
+- PR #195 did not add runtime code, public CLI commands, deterministic gates, workflow states, Pattern Advisor implementation, or pattern catalog behavior.
 
-- `162 passed`
+Latest verified local gates after PR #195:
+
+- `166 passed`
 - `ruff check .` passed
 - `agentic-kit check-docs` passed
 - `agentic-kit doctor` passed
@@ -182,13 +171,9 @@ This handoff intentionally keeps coverage terms visible for deterministic gates:
 
 ## Current Branch Work
 
-Prepared files should include:
-
-- `pyproject.toml` and `src/agentic_project_kit/__init__.py` bumped to 0.3.7.
-- `CITATION.cff` updated with the verified v0.3.7 version DOI.
-- `CHANGELOG.md`, `README.md`, `docs/STATUS.md`, and `docs/handoff/CURRENT_HANDOFF.md` updated for post-release v0.3.7 DOI metadata.
+Completed post-v0.3.9 work now includes PR #195, which added `docs/ideas/DIDACTIC_GUIDANCE.md` as a documentation-only, non-binding didactic orientation note and cross-linked it from state, handoff, and agent guidance docs.
 
-No Pattern Advisor MVP, DCO implementation, or additional Guided CLI runtime change is part of this branch.
+No Pattern Advisor MVP, DCO implementation, public CLI command, new deterministic gate, workflow state, or runtime behavior change is part of this didactic guidance foundation work.
 
 ## Next Safe Step
 
diff --git a/docs/reports/post_didactic_guidance_state_diff.md b/docs/reports/post_didactic_guidance_state_diff.md
new file mode 100644
index 0000000..e420c22
--- /dev/null
+++ b/docs/reports/post_didactic_guidance_state_diff.md
@@ -0,0 +1,124 @@
+diff --git a/docs/STATUS.md b/docs/STATUS.md
+index f048f7a..38f88c0 100644
+--- a/docs/STATUS.md
++++ b/docs/STATUS.md
+@@ -61,6 +61,7 @@ The latest verified gates before v0.3.7 release preparation were:
+ - PR #170 added read-only `agentic-kit workflow status --explain`, documented it, and raised the suite to 160 tests.
+ - PR #171 refreshed current-state and handoff documentation after PR #170.
+ - PR #172 completed Guided Workflow Usability v1 and raised the suite to 162 tests.
++- PR #195 added `docs/ideas/DIDACTIC_GUIDANCE.md` as a documentation-only, non-binding didactic orientation note and cross-linked it from state, handoff, and agent guidance docs.
+ 
+ ## Idea-note state
+ 
+@@ -70,6 +71,7 @@ The repository has four related non-binding architecture idea notes:
+ - `docs/ideas/DETERMINISTIC_CELL_ORCHESTRATION.md`
+ - `docs/ideas/LAYERED_CLI_USABILITY.md`
+ - `docs/ideas/PATTERN_ADVISOR.md`
++- `docs/ideas/DIDACTIC_GUIDANCE.md`
+ 
+ These documents preserve architecture options without making them automatic implementation requirements.
+ 
+@@ -213,12 +215,12 @@ Project-level state documentation is machine-checkable:
+ 
+ ## Current Goal
+ 
+-v0.3.9 is released and post-release verified. GitHub Release exists, and Zenodo verified version DOI is `10.5281/zenodo.20210345`.
++v0.3.9 is released and post-release verified. GitHub Release exists, Zenodo verified version DOI is `10.5281/zenodo.20210345`, and PR #195 has added the didactic guidance foundation note on main.
+ 
+ ## Current Blockers
+ 
+-- Local gates must pass on `docs/record-v0.3.7-doi`.
+-- Release metadata, package version, citation metadata, changelog, status, and handoff must agree before tagging.
++- No current blockers are known after PR #195.
++- Next work should start from a new narrow slice with an explicit command-level contract.
+ 
+ ## Live Status Commands
+ 
+diff --git a/docs/handoff/CURRENT_HANDOFF.md b/docs/handoff/CURRENT_HANDOFF.md
+index aa1e3cc..6e4529a 100644
+--- a/docs/handoff/CURRENT_HANDOFF.md
++++ b/docs/handoff/CURRENT_HANDOFF.md
+@@ -9,46 +9,35 @@ Base branch: main
+ 
+ ## Current Goal
+ 
+-v0.3.9 is released and post-release verified. GitHub Release exists, and Zenodo verified version DOI is `10.5281/zenodo.20210345`.
+-
+-v0.3.7 is complete. The v0.3.8 planning note is merged on main, and the first narrowly scoped Guided CLI Usability v2 slice is merged on main.
++v0.3.9 is released and post-release verified. GitHub Release exists, Zenodo verified version DOI is `10.5281/zenodo.20210345`, and PR #195 has added the didactic guidance foundation note on main.
+ 
+ ## Current Repository State
+ 
+-v0.3.7 is released and post-release verified. Verified v0.3.7 version DOI: `10.5281/zenodo.20206581`. The post-release Zenodo verification is complete for v0.3.7.
+-
+-Verified release evidence:
+-
+-- GitHub Release v0.3.7 exists.
+-- Zenodo concept DOI: `10.5281/zenodo.20101359`.
+-- Verified v0.3.7 version DOI: `10.5281/zenodo.20206581`.
+-- `agentic-kit post-release-check --version 0.3.7` passed.
+-- PR #163 recorded the verified v0.3.6 DOI metadata on main.
+-
+-Post-release work completed after v0.3.6:
+-
+-- PR #164 preserved `docs/ideas/DETERMINISTIC_CELL_ORCHESTRATION.md` as a curated idea note.
+-- PR #164 introduced `docs/ideas/LAYERED_CLI_USABILITY.md` as a non-binding usability-layer model.
+-- PR #164 added small `AGENTS.md` cross-references to the DCO and layered CLI usability idea notes.
+-- PR #165 refreshed `docs/STATUS.md` and `docs/handoff/CURRENT_HANDOFF.md` after the idea-note merge.
+-- PR #166 hardened `agentic-kit workflow cleanup` so stale `temp/workflow-evidence-*` branches can be removed even when `.agentic/workflow_state` is already `IDLE`.
+-- PR #167 refreshed `docs/STATUS.md` and `docs/handoff/CURRENT_HANDOFF.md` after workflow cleanup hardening.
+-- PR #168 added `docs/ideas/PATTERN_ADVISOR.md` as a non-binding idea note / architecture research track.
+-- PR #170 added read-only `agentic-kit workflow status --explain` guidance for common workflow states.
+-- PR #171 refreshed `docs/STATUS.md` and `docs/handoff/CURRENT_HANDOFF.md` after PR #170.
+-- PR #172 completed Guided Workflow Usability v1 with read-only safety wording, `current_report` explanation, a README quick command guide, and a guided status compass.
+-
+-The v0.3.7 release-preparation PR was merged on main after:
++Current main head after PR #195:
+ 
+ ```text
+-0161838 Complete guided workflow status usability (#172)
+-a2d5e68 Update status and handoff after workflow status explain (#171)
+-1d0c5f4 Explain workflow status next steps (#170)
++401e98d Add didactic guidance foundation note (#195)
++d877802 Finalize post-v0.3.9 DOI state (#194)
++fa386b6 Record v0.3.9 DOI metadata (#193)
++bb15d82 tag: v0.3.9, Finalize pre-v0.3.9 release state (#192)
++ef72e37 Prepare v0.3.9 release metadata (#191)
++239047d Finalize post-repo-ns-entrypoint state (#190)
++68614a3 Add repo ns compatibility entrypoint (#189)
++7660db5 Finalize post-failed-status-guidance state (#188)
+ ```
+ 
+-Latest verified local gates after v0.3.7 release preparation:
++Verified release and post-merge evidence:
++
++- GitHub Release v0.3.9 exists.
++- Zenodo concept DOI: `10.5281/zenodo.20101359`.
++- Verified v0.3.9 version DOI: `10.5281/zenodo.20210345`.
++- `agentic-kit post-release-check --version 0.3.9` passed before PR #195.
++- PR #195 added `docs/ideas/DIDACTIC_GUIDANCE.md` as a documentation-only, non-binding didactic orientation note.
++- PR #195 did not add runtime code, public CLI commands, deterministic gates, workflow states, Pattern Advisor implementation, or pattern catalog behavior.
+ 
+-- `162 passed`
++Latest verified local gates after PR #195:
++
++- `166 passed`
+ - `ruff check .` passed
+ - `agentic-kit check-docs` passed
+ - `agentic-kit doctor` passed
+@@ -182,13 +171,9 @@ This handoff intentionally keeps coverage terms visible for deterministic gates:
+ 
+ ## Current Branch Work
+ 
+-Prepared files should include:
+-
+-- `pyproject.toml` and `src/agentic_project_kit/__init__.py` bumped to 0.3.7.
+-- `CITATION.cff` updated with the verified v0.3.7 version DOI.
+-- `CHANGELOG.md`, `README.md`, `docs/STATUS.md`, and `docs/handoff/CURRENT_HANDOFF.md` updated for post-release v0.3.7 DOI metadata.
++Completed post-v0.3.9 work now includes PR #195, which added `docs/ideas/DIDACTIC_GUIDANCE.md` as a documentation-only, non-binding didactic orientation note and cross-linked it from state, handoff, and agent guidance docs.
+ 
+-No Pattern Advisor MVP, DCO implementation, or additional Guided CLI runtime change is part of this branch.
++No Pattern Advisor MVP, DCO implementation, public CLI command, new deterministic gate, workflow state, or runtime behavior change is part of this didactic guidance foundation work.
+ 
+ ## Next Safe Step
+ 
