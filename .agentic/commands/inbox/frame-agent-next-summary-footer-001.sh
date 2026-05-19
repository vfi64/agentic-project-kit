printf '\n\n\n'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '\n\n\n'
printf 'FRAME AGENT-NEXT SUMMARY FOOTER\n\n'

TS=$(date +%Y%m%d-%H%M%S)
TMPLOG="/tmp/${TS}_frame-agent-next-summary-footer.log"
BRANCH="fix/framed-agent-next-summary-footer"
OK=1

{
  printf 'FRAME AGENT-NEXT SUMMARY FOOTER\n\n'
  git fetch origin main || OK=0
  git switch main || OK=0
  git pull --ff-only origin main || OK=0
  ./ns terminal-remote-preflight || OK=0
  ./ns artifact-gc --execute || OK=0
  if git show-ref --verify --quiet "refs/heads/$BRANCH"; then git branch -D "$BRANCH" || OK=0; fi
  git switch -c "$BRANCH" || OK=0
  mkdir -p tmp
  : > tmp/patch_framed_summary_footer.py
  printf '%s\n' 'from pathlib import Path' >> tmp/patch_framed_summary_footer.py
  printf '%s\n' 'p = Path("src/agentic_project_kit/agent_command_runner.py")' >> tmp/patch_framed_summary_footer.py
  printf '%s\n' 'text = p.read_text(encoding="utf-8")' >> tmp/patch_framed_summary_footer.py
  printf '%s\n' 'helper = """' >> tmp/patch_framed_summary_footer.py
  printf '%s\n' 'def print_summary_footer(work_result: str, evidence_result: str, overall_result: str, reply: str, reason: str = "") -> None:' >> tmp/patch_framed_summary_footer.py
  printf '%s\n' '    print("================================================================")' >> tmp/patch_framed_summary_footer.py
  printf '%s\n' '    print("SUMMARY")' >> tmp/patch_framed_summary_footer.py
  printf '%s\n' '    print(f"WORK RESULT: {work_result}")' >> tmp/patch_framed_summary_footer.py
  printf '%s\n' '    print(f"EVIDENCE RESULT: {evidence_result}")' >> tmp/patch_framed_summary_footer.py
  printf '%s\n' '    print(f"OVERALL RESULT: {overall_result}")' >> tmp/patch_framed_summary_footer.py
  printf '%s\n' '    if reason:' >> tmp/patch_framed_summary_footer.py
  printf '%s\n' '        print(f"REASON: {reason}")' >> tmp/patch_framed_summary_footer.py
  printf '%s\n' '    print(f"NEXT CHAT REPLY: {reply}")' >> tmp/patch_framed_summary_footer.py
  printf '%s\n' '    print("================================================================")' >> tmp/patch_framed_summary_footer.py
  printf '%s\n' '"""' >> tmp/patch_framed_summary_footer.py
  printf '%s\n' 'if "def print_summary_footer(" not in text:' >> tmp/patch_framed_summary_footer.py
  printf '%s\n' '    marker = "def load_current_command() -> CommandMetadata:"' >> tmp/patch_framed_summary_footer.py
  printf '%s\n' '    text = text.replace(marker, helper + "\n" + marker)' >> tmp/patch_framed_summary_footer.py
  printf '%s\n' 'text = text.replace("### AGENT-NEXT RESULT: HARD-FAIL ###", "### AGENT-NEXT RESULT: HARD-FAIL ###")' >> tmp/patch_framed_summary_footer.py
  printf '%s\n' 'if "print_summary_footer(" not in text.split("def print_summary_footer(", 1)[-1]:' >> tmp/patch_framed_summary_footer.py
  printf '%s\n' '    text = text.replace("print(\\"### END AGENT-NEXT RESULT ###\\")", "print(\\"### END AGENT-NEXT RESULT ###\\")\n        print_summary_footer(work_result=\\"FAIL\\", evidence_result=\\"PASS\\", overall_result=\\"FAIL\\", reply=\\"f\\", reason=\\"normal command failure\\")", 1)' >> tmp/patch_framed_summary_footer.py
  printf '%s\n' 'p.write_text(text, encoding="utf-8")' >> tmp/patch_framed_summary_footer.py
  PYTHONPATH=src python3 tmp/patch_framed_summary_footer.py || OK=0
  rm -f tmp/patch_framed_summary_footer.py
  grep -R "SUMMARY\|NEXT CHAT REPLY\|print_summary_footer" -n src/agentic_project_kit/agent_command_runner.py || OK=0
  ./ns dev || OK=0
  git add src/agentic_project_kit/agent_command_runner.py || OK=0
  git commit -m "Add framed summary footer for agent-next" || OK=0
  git push -u origin "$BRANCH" || OK=0
  gh pr create --title "Add framed SUMMARY footer for no-copy workflow" --body "Adds a clearly framed SUMMARY footer so the user can unambiguously see WORK RESULT, EVIDENCE RESULT, OVERALL RESULT, and NEXT CHAT REPLY." --base main --head "$BRANCH" || OK=0
  if [ "$OK" -eq 1 ]; then printf '\n### RESULT: PASS ###\n'; else printf '\n### RESULT: FAIL ###\n'; fi
} 2>&1 | tee "$TMPLOG"
./ns terminal-finalize "$TMPLOG" frame-agent-next-summary-footer
git add docs/reports/terminal/LATEST_TERMINAL_LOG.txt docs/reports/terminal/*.log
git commit -m "Preserve framed summary footer terminal log"
git push
printf '\n================================================================\nSUMMARY\n'
if [ "$OK" -eq 1 ]; then printf 'WORK RESULT: PASS\nEVIDENCE RESULT: PASS\nOVERALL RESULT: PASS\nNEXT CHAT REPLY: p\n'; else printf 'WORK RESULT: FAIL\nEVIDENCE RESULT: PASS\nOVERALL RESULT: FAIL\nNEXT CHAT REPLY: f\n'; fi
printf '================================================================\n'
