diff --git a/README.md b/README.md
index b31d8d7..192b66a 100644
--- a/README.md
+++ b/README.md
@@ -279,7 +279,7 @@ Quick command guide:
 - `workflow cleanup`: clean uploaded temporary evidence after review.
 - `workflow fail-report`: upload preserved FAILED-state evidence for diagnosis without cleanup or retry.
 
-The workflow uses `.agentic/workflow_state` and `.agentic/current_work.yaml`. `IDLE` with `current_work.yaml` state `READY` is a safe no-op. A run starts only after an explicit request, for example `agentic-kit workflow request`, followed by `agentic-kit workflow run`. A requested run captures bounded local evidence, resets the request to `READY`, updates `docs/reports/CURRENT_WORKFLOW_OUTPUT.md`, uploads a temporary evidence branch, and waits for explicit cleanup.
+The workflow uses `.agentic/workflow_state` and `.agentic/current_work.yaml`. `IDLE` with `current_work.yaml` state `READY` is a safe no-op. A run starts only after an explicit request. The explicit two-step form is `agentic-kit workflow request`, followed by `agentic-kit workflow run`. The shortcut `agentic-kit workflow go` performs the same request-and-run handoff for one bounded workflow step. A requested run captures bounded local evidence, resets the request to `READY`, updates `docs/reports/CURRENT_WORKFLOW_OUTPUT.md`, uploads a temporary evidence branch, and waits for explicit cleanup. When bounded local output already exists and should be uploaded without pasted terminal output, use `agentic-kit workflow upload-output` or the repo-local shortcut `./ns upload`.
 
 Legacy compatibility remains available through:
 
diff --git a/docs/DOCUMENTATION_COVERAGE.yaml b/docs/DOCUMENTATION_COVERAGE.yaml
index 5f281d2..e713961 100644
--- a/docs/DOCUMENTATION_COVERAGE.yaml
+++ b/docs/DOCUMENTATION_COVERAGE.yaml
@@ -25,6 +25,8 @@ rules:
           - agentic-kit todo list
           - agentic-kit todo complete
           - agentic-kit todo render
+          - agentic-kit workflow go
+          - agentic-kit workflow upload-output
           - agentic-kit workflow request
           - agentic-kit workflow run
           - agentic-kit workflow status
diff --git a/docs/WORKFLOW_OUTPUT_CYCLE.md b/docs/WORKFLOW_OUTPUT_CYCLE.md
index b2e7289..e242738 100644
--- a/docs/WORKFLOW_OUTPUT_CYCLE.md
+++ b/docs/WORKFLOW_OUTPUT_CYCLE.md
@@ -136,6 +136,13 @@ The repository provides `./ns` as the versioned compatibility entrypoint. It del
 
 After adding those aliases to `~/.zshrc`, routine compatibility-entrypoint work becomes:
 
+```zsh
+./ns go
+./ns upload
+```
+
+The older compatibility form remains available when a split request/run cycle is useful:
+
 ```zsh
 ./ns --request
 ./ns
@@ -165,6 +172,8 @@ It does not switch to `main`, so it can validate either `main` or the current PR
 Use these commands for explicit operation:
 
 ```text
+agentic-kit workflow go
+agentic-kit workflow upload-output
 agentic-kit workflow request
 agentic-kit workflow run
 agentic-kit workflow status
@@ -173,6 +182,8 @@ agentic-kit workflow cleanup
 
 The commands operate on `.agentic/workflow_state` and `.agentic/current_work.yaml`.
 
+`agentic-kit workflow go` is the normal shortcut for the chat-assisted workflow: it sets `.agentic/current_work.yaml` to `state: REQUESTED` and runs one bounded workflow step. It replaces the routine manual sequence `workflow request` plus `workflow run` without removing either explicit command. `agentic-kit workflow upload-output` uploads the latest bounded local workflow evidence for review, so terminal output does not need to be pasted into chat when a local evidence file exists.
+
 `agentic-kit workflow request` is the public equivalent of `tools/next-step.py --request`: it sets `.agentic/current_work.yaml` to `state: REQUESTED` while leaving `.agentic/workflow_state` at `IDLE`. It does not run the workflow as a side effect. A repeated request while the workflow is already requested is idempotent.
 
 `agentic-kit workflow status` reports both state layers. Add `--explain` for a read-only interpretation and recommended next step. The explanation must remain read-only: for dirty working trees and failed workflow states it should recommend inspection before any workflow automation. For example:
@@ -199,6 +210,8 @@ Guided status compass:
 - `FAILED`: run `agentic-kit workflow fail-report` when bounded local evidence exists, then stop and inspect evidence before cleanup or retry.
 - dirty working tree: inspect `git status` before running workflow automation.
 
+- `workflow go`: requests the configured declarative workflow and runs one bounded state-machine step.
+- `workflow upload-output`: uploads the latest bounded local workflow evidence without requiring pasted terminal output.
 - `workflow request`: marks the declarative workflow file as REQUESTED while the main workflow state remains IDLE.
 - `workflow run`: runs exactly one bounded state-machine step through the existing local entrypoint.
 - `workflow status`: prints the current state, current workflow request state, and bounded evidence pointers.
diff --git a/ns b/ns
index b434e09..b1cac20 100755
--- a/ns
+++ b/ns
@@ -2,6 +2,20 @@
 set -eu
 SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
 cd "$SCRIPT_DIR"
+if [ "${1:-}" = "go" ]; then
+  shift
+  if [ -x ".venv/bin/agentic-kit" ]; then
+    exec .venv/bin/agentic-kit workflow go "$@"
+  fi
+  exec agentic-kit workflow go "$@"
+fi
+if [ "${1:-}" = "upload" ]; then
+  shift
+  if [ -x ".venv/bin/agentic-kit" ]; then
+    exec .venv/bin/agentic-kit workflow upload-output "$@"
+  fi
+  exec agentic-kit workflow upload-output "$@"
+fi
 if [ -x ".venv/bin/python" ]; then
   exec .venv/bin/python tools/next-step.py "$@"
 fi
diff --git a/src/agentic_project_kit/cli_commands/workflow.py b/src/agentic_project_kit/cli_commands/workflow.py
index ed5e046..2b8ad36 100644
--- a/src/agentic_project_kit/cli_commands/workflow.py
+++ b/src/agentic_project_kit/cli_commands/workflow.py
@@ -219,6 +219,23 @@ def workflow_run(
     raise typer.Exit(code=_run_next_step(project_root.resolve()))
 
 
+@workflow_app.command("go")
+def workflow_go(
+    project_root: Path = typer.Option(Path("."), "--root", help="Project root containing .agentic/current_work.yaml and tools/next-step.py."),
+) -> None:
+    """Request the configured workflow and run one bounded step."""
+    root = project_root.resolve()
+    state = _read_state(root)
+    if state != "IDLE":
+        raise typer.BadParameter(f"refusing to start workflow from state: {state}")
+    _workflow_request_state(root)
+    _set_workflow_request_state(root, "REQUESTED")
+    typer.echo(f"Current workflow request file: {WORK_FILE}")
+    typer.echo("Workflow request state: REQUESTED")
+    typer.echo("Running one bounded workflow step.")
+    raise typer.Exit(code=_run_next_step(root))
+
+
 @workflow_app.command("status")
 def workflow_status(
     project_root: Path = typer.Option(Path("."), "--root", help="Project root containing .agentic/workflow_state."),
@@ -257,6 +274,21 @@ def workflow_fail_report(
     raise typer.Exit(code=_run_next_step(root, ["--fail-report"]))
 
 
+@workflow_app.command("upload-output")
+def workflow_upload_output(
+    project_root: Path = typer.Option(Path("."), "--root", help="Project root containing tools/next-step.py."),
+) -> None:
+    """Upload the latest bounded local workflow output evidence for review."""
+    root = project_root.resolve()
+    state = _read_state(root)
+    if state == "UPLOADED":
+        raise typer.BadParameter("output evidence is already uploaded; run workflow cleanup after review")
+    if state == "CLEANUP":
+        raise typer.BadParameter("workflow cleanup is already pending")
+    typer.echo("Uploading latest bounded workflow output evidence.")
+    raise typer.Exit(code=_run_next_step(root, ["--upload-output"]))
+
+
 @workflow_app.command("cleanup")
 def workflow_cleanup(
     project_root: Path = typer.Option(Path("."), "--root", help="Project root containing tools/next-step.py."),
diff --git a/tests/test_workflow_request_cli.py b/tests/test_workflow_request_cli.py
index 2863916..5775c91 100644
--- a/tests/test_workflow_request_cli.py
+++ b/tests/test_workflow_request_cli.py
@@ -151,3 +151,78 @@ def test_workflow_status_explain_describes_current_report(tmp_path: Path) -> Non
     assert result.exit_code == 0
     assert "current_report=docs/reports/CURRENT_WORKFLOW_OUTPUT.md" in result.output
     assert "current_report points to the latest local workflow-output summary." in result.output
+
+
+
+def test_workflow_go_requests_and_runs_one_bounded_step(tmp_path: Path, monkeypatch) -> None:
+    _write_workflow_files(tmp_path)
+    calls: list[tuple[Path, list[str] | None]] = []
+
+    def fake_run_next_step(root: Path, extra_args: list[str] | None = None) -> int:
+        calls.append((root, extra_args))
+        return 0
+
+    import agentic_project_kit.cli_commands.workflow as workflow_module
+
+    monkeypatch.setattr(workflow_module, "_run_next_step", fake_run_next_step)
+    result = runner.invoke(app, ["workflow", "go", "--root", str(tmp_path)])
+
+    assert result.exit_code == 0
+    assert "Workflow request state: REQUESTED" in result.output
+    assert "Running one bounded workflow step." in result.output
+    assert "state: REQUESTED" in (tmp_path / ".agentic" / "current_work.yaml").read_text(encoding="utf-8")
+    assert calls == [(tmp_path.resolve(), None)]
+
+
+def test_workflow_go_refuses_non_idle_workflow_state(tmp_path: Path, monkeypatch) -> None:
+    _write_workflow_files(tmp_path, workflow_state="FAILED")
+    calls: list[tuple[Path, list[str] | None]] = []
+
+    def fake_run_next_step(root: Path, extra_args: list[str] | None = None) -> int:
+        calls.append((root, extra_args))
+        return 0
+
+    import agentic_project_kit.cli_commands.workflow as workflow_module
+
+    monkeypatch.setattr(workflow_module, "_run_next_step", fake_run_next_step)
+    result = runner.invoke(app, ["workflow", "go", "--root", str(tmp_path)])
+
+    assert result.exit_code != 0
+    assert "refusing to start workflow from state: FAILED" in result.output
+    assert calls == []
+
+
+def test_workflow_upload_output_uploads_latest_bounded_output(tmp_path: Path, monkeypatch) -> None:
+    _write_workflow_files(tmp_path)
+    calls: list[tuple[Path, list[str] | None]] = []
+
+    def fake_run_next_step(root: Path, extra_args: list[str] | None = None) -> int:
+        calls.append((root, extra_args))
+        return 0
+
+    import agentic_project_kit.cli_commands.workflow as workflow_module
+
+    monkeypatch.setattr(workflow_module, "_run_next_step", fake_run_next_step)
+    result = runner.invoke(app, ["workflow", "upload-output", "--root", str(tmp_path)])
+
+    assert result.exit_code == 0
+    assert "Uploading latest bounded workflow output evidence." in result.output
+    assert calls == [(tmp_path.resolve(), ["--upload-output"])]
+
+
+def test_workflow_upload_output_refuses_already_uploaded_state(tmp_path: Path, monkeypatch) -> None:
+    _write_workflow_files(tmp_path, workflow_state="UPLOADED")
+    calls: list[tuple[Path, list[str] | None]] = []
+
+    def fake_run_next_step(root: Path, extra_args: list[str] | None = None) -> int:
+        calls.append((root, extra_args))
+        return 0
+
+    import agentic_project_kit.cli_commands.workflow as workflow_module
+
+    monkeypatch.setattr(workflow_module, "_run_next_step", fake_run_next_step)
+    result = runner.invoke(app, ["workflow", "upload-output", "--root", str(tmp_path)])
+
+    assert result.exit_code != 0
+    assert "output evidence is already uploaded" in result.output
+    assert calls == []
diff --git a/tools/next-step.py b/tools/next-step.py
index 444d18d..705d34f 100755
--- a/tools/next-step.py
+++ b/tools/next-step.py
@@ -177,6 +177,17 @@ def step_fail_report() -> None:
     print("Next state: UPLOADED")
 
 
+def step_upload_output() -> None:
+    state = read_state()
+    if state in {"UPLOADED", "CLEANUP"}:
+        raise SystemExit(f"upload-output requires local evidence before upload cleanup, got {state}")
+    evidence = latest_evidence()
+    write_current_report(evidence, "Bounded local workflow output uploaded for review without pasted terminal output.")
+    branch = create_evidence_branch("UPLOADED")
+    print(f"Uploaded workflow output evidence branch: {branch}")
+    print("Next state: UPLOADED")
+
+
 def workflow_request_state() -> str:
     if not WORKFLOW_FILE.exists():
         return "MISSING"
@@ -241,8 +252,12 @@ def main() -> int:
         ensure_project_environment()
         step_fail_report()
         return 0
+    if sys.argv[1:] == ["--upload-output"]:
+        ensure_project_environment()
+        step_upload_output()
+        return 0
     if sys.argv[1:]:
-        raise SystemExit("Usage: next-step.py [--request|--fail-report]")
+        raise SystemExit("Usage: next-step.py [--request|--fail-report|--upload-output]")
     ensure_project_environment()
     state = read_state()
     print(f"workflow_state={state}")
