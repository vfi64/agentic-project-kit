printf '\n\n\n'
printf '-------------------------------------------------------------------------\n'
printf '-------------------------------------------------------------------------\n'
printf '-------------------------------------------------------------------------\n'
printf '\n\n\n'
printf 'HARDEN RELEASE VERSION SOURCE CONTRACT\n\n'

OK=1
BRANCH="fix/release-version-source-contract"

printf '### CREATE FEATURE BRANCH WITHOUT SWITCH COMMAND ###\n'
git checkout -b "$BRANCH" || OK=0

printf '\n### WRITE PATCH SCRIPT ###\n'
mkdir -p tmp
: > tmp/harden_release_version_source_contract.py

printf '%s\n' 'from pathlib import Path' >> tmp/harden_release_version_source_contract.py
printf '%s\n' 'import re' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '' >> tmp/harden_release_version_source_contract.py
printf '%s\n' 'release = Path("src/agentic_project_kit/release.py")' >> tmp/harden_release_version_source_contract.py
printf '%s\n' 'text = release.read_text(encoding="utf-8")' >> tmp/harden_release_version_source_contract.py
printf '%s\n' 'needle = "check_file_contains(project_root / \\"pyproject.toml\\", f'\''version = \\"{resolved_version}\\"'\'', \\"pyproject version\\"),"' >> tmp/harden_release_version_source_contract.py
printf '%s\n' 'insert = needle + "\\n        check_file_contains(project_root / \\"src/agentic_project_kit/__init__.py\\", f'\''__version__ = \\"{resolved_version}\\"'\'', \\"package __version__\\"),"' >> tmp/harden_release_version_source_contract.py
printf '%s\n' 'if "package __version__" not in text:' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    if needle not in text:' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '        raise SystemExit("release.py pyproject check marker not found")' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    text = text.replace(needle, insert)' >> tmp/harden_release_version_source_contract.py
printf '%s\n' 'release.write_text(text, encoding="utf-8")' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '' >> tmp/harden_release_version_source_contract.py
printf '%s\n' 'prep = Path("tools/ns_release_metadata_prep.py")' >> tmp/harden_release_version_source_contract.py
printf '%s\n' 'prep_text = prep.read_text(encoding="utf-8")' >> tmp/harden_release_version_source_contract.py
printf '%s\n' 'if "src/agentic_project_kit/__init__.py" not in prep_text:' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    marker = "update_pyproject(project_root / \\"pyproject.toml\\", version)"' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    addition = marker + "\\n    update_init_version(project_root / \\"src/agentic_project_kit/__init__.py\\", version)"' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    if marker not in prep_text:' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '        raise SystemExit("release metadata prep pyproject marker not found")' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    prep_text = prep_text.replace(marker, addition)' >> tmp/harden_release_version_source_contract.py
printf '%s\n' 'if "def update_init_version(" not in prep_text:' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    helper_marker = "def update_pyproject(path: Path, version: str) -> None:"' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    helper = "def update_init_version(path: Path, version: str) -> None:\\n    text = path.read_text(encoding=\\"utf-8\\")\\n    new_text = re.sub(r'\''^__version__\\\\s*=\\\\s*[\\"\\\\'\''][^\\"\\\\'\'']+[\\"\\\\'\'']'\'', f'\''__version__ = \\"{version}\\"'\'', text, count=1, flags=re.MULTILINE)\\n    if new_text == text:\\n        raise SystemExit(f\\"missing package __version__ assignment in {path}\\")\\n    path.write_text(new_text, encoding=\\"utf-8\\")\\n\\n" + helper_marker' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    if helper_marker not in prep_text:' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '        raise SystemExit("release metadata prep helper marker not found")' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    prep_text = prep_text.replace(helper_marker, helper)' >> tmp/harden_release_version_source_contract.py
printf '%s\n' 'prep.write_text(prep_text, encoding="utf-8")' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '' >> tmp/harden_release_version_source_contract.py
printf '%s\n' 'test = Path("tests/test_release_version_source_contract.py")' >> tmp/harden_release_version_source_contract.py
printf '%s\n' 'test.write_text("""from pathlib import Path' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '' >> tmp/harden_release_version_source_contract.py
printf '%s\n' 'from agentic_project_kit.release import evaluate_release_state, render_release_report' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '' >> tmp/harden_release_version_source_contract.py
printf '%s\n' 'def write_release_fixture(root: Path, version: str, init_version: str | None = None) -> None:' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    init_version = version if init_version is None else init_version' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    (root / "src/agentic_project_kit").mkdir(parents=True)' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    (root / "pyproject.toml").write_text(f'\''version = "{version}"\\\\n'\'', encoding="utf-8")' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    (root / "src/agentic_project_kit/__init__.py").write_text(f'\''__version__ = "{init_version}"\\\\n'\'', encoding="utf-8")' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    (root / "CHANGELOG.md").write_text(f"## v{version}\\\\n", encoding="utf-8")' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    (root / "README.md").write_text(f"Version `{version}`\\\\n", encoding="utf-8")' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    (root / "CITATION.cff").write_text(f"version: {version}\\\\n", encoding="utf-8")' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    (root / "docs").mkdir()' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    (root / "docs/STATUS.md").write_text(f"Current version: {version}\\\\n", encoding="utf-8")' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    (root / "docs/handoff").mkdir(parents=True)' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    (root / "docs/handoff/CURRENT_HANDOFF.md").write_text(f"Current version: {version}\\\\n", encoding="utf-8")' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '' >> tmp/harden_release_version_source_contract.py
printf '%s\n' 'def test_release_check_requires_package_init_version(tmp_path):' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    write_release_fixture(tmp_path, "1.2.3", init_version="1.2.2")' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    report = evaluate_release_state(tmp_path, "1.2.3")' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    rendered = render_release_report(report)' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    assert not report.ok' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    assert "[FAIL] package __version__" in rendered' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '' >> tmp/harden_release_version_source_contract.py
printf '%s\n' 'def test_release_check_accepts_matching_package_init_version(tmp_path):' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    write_release_fixture(tmp_path, "1.2.3")' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    report = evaluate_release_state(tmp_path, "1.2.3")' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    rendered = render_release_report(report)' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '    assert "[PASS] package __version__" in rendered' >> tmp/harden_release_version_source_contract.py
printf '%s\n' '""", encoding="utf-8")' >> tmp/harden_release_version_source_contract.py

printf '\n### RUN PATCH SCRIPT ###\n'
.venv/bin/python tmp/harden_release_version_source_contract.py || OK=0
rm -f tmp/harden_release_version_source_contract.py

printf '\n### VERIFY PATCH CONTENT ###\n'
grep -R "package __version__\|update_init_version\|test_release_check_requires_package_init_version" -n src/agentic_project_kit/release.py tools/ns_release_metadata_prep.py tests/test_release_version_source_contract.py || OK=0

printf '\n### LOCAL GATES ###\n'
.venv/bin/python -m pytest -q tests/test_release.py tests/test_release_version_source_contract.py || OK=0
./ns release-gate 0.3.27 || OK=0
./ns command-inbox-check || OK=0
./ns artifact-gc || OK=0
./ns state-freshness-check || OK=0
./ns handoff-check || OK=0
./ns governance-check || OK=0
./ns dev || OK=0

printf '\n### COMMIT PATCH ###\n'
git status --short || OK=0
git add src/agentic_project_kit/release.py tools/ns_release_metadata_prep.py tests/test_release_version_source_contract.py || OK=0
git commit -m "Harden release version source contract" || OK=0

printf '\n### PUSH AND CREATE PR ###\n'
./ns terminal-remote-preflight || OK=0
git push -u origin "$BRANCH" || OK=0
gh pr create --title "Harden release version source contract" --body "Adds package __version__ to release-check and release-prep contract with regression coverage for pyproject/__init__.py divergence." --base main --head "$BRANCH" || OK=0

if [ "$OK" -eq 1 ]
then
  printf '\n================================================================\n'
  printf 'SUMMARY\n'
  printf 'WORK RESULT: PASS\n'
  printf 'EVIDENCE RESULT: PASS\n'
  printf 'OVERALL RESULT: PASS\n'
  printf 'NEXT CHAT REPLY: p\n'
  printf '================================================================\n'
  exit 0
fi

printf '\n================================================================\n'
printf 'SUMMARY\n'
printf 'WORK RESULT: FAIL\n'
printf 'EVIDENCE RESULT: FAIL\n'
printf 'OVERALL RESULT: FAIL\n'
printf 'NEXT CHAT REPLY: f\n'
printf '================================================================\n'
exit 1
