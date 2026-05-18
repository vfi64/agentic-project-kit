printf '\n\n\n'
printf '-------------------------------------------------------------------------\n'
printf '-------------------------------------------------------------------------\n'
printf '-------------------------------------------------------------------------\n'
printf '\n\n\n'
printf 'NO-COPY E2E PROTOCOL PATCH: LATEST COMMAND RUN POINTER\n\n'

OK=0
BRANCH='fix/no-copy-result-handoff-pointer'

printf '### START STATE ###\n'
git branch --show-current || OK=1
git status --short || OK=1

printf '\n### SYNC MAIN ###\n'
git fetch origin main || OK=1

printf '\n### SWITCH FEATURE BRANCH ###\n'
if git show-ref --verify --quiet refs/heads/$BRANCH
then
  git switch $BRANCH || OK=1
else
  git switch -c $BRANCH origin/main || OK=1
fi

printf '\n### WRITE PATCH SCRIPT ###\n'
printf '%s' 'ZnJvbSBwYXRobGliIGltcG9ydCBQYXRoCgpydW5uZXIgPSBQYXRoKCJzcmMvYWdlbnRpY19wcm9qZWN0X2tpdC9hZ2VudF9jb21tYW5kX3J1bm5lci5weSIpCnRleHQgPSBydW5uZXIucmVhZF90ZXh0KGVuY29kaW5nPSJ1dGYtOCIpCmlmICdMQVRFU1RfQ09NTUFORF9QT0lOVEVSID0gUkVQT1JUX0RJUiAvICJMQVRFU1RfQ09NTUFORF9SVU4udHh0Iicgbm90IGluIHRleHQ6CiAgICB0ZXh0ID0gdGV4dC5yZXBsYWNlKCdSRVBPUlRfRElSID0gUGF0aCgiZG9jcy9yZXBvcnRzL2NvbW1hbmRfcnVucyIpXFxuJywgJ1JFUE9SVF9ESVIgPSBQYXRoKCJkb2NzL3JlcG9ydHMvY29tbWFuZF9ydW5zIilcXG5MQVRFU1RfQ09NTUFORF9QT0lOVEVSID0gUkVQT1JUX0RJUiAvICJMQVRFU1RfQ09NTUFORF9SVU4udHh0IlxcbicpCmlmICdMQVRFU1RfQ09NTUFORF9QT0lOVEVSLndyaXRlX3RleHQocGF0aC5hc19wb3NpeCgpICsgIlxcXFxuIiwgZW5jb2Rpbmc9InV0Zi04IiknIG5vdCBpbiB0ZXh0OgogICAgdGV4dCA9IHRleHQucmVwbGFjZSgnICAgIHBhdGgud3JpdGVfdGV4dCgiXFxcXG4iLmpvaW4obGluZXMpICsgIlxcXFxuIiwgZW5jb2Rpbmc9InV0Zi04IilcXG4gICAgcmV0dXJuIHBhdGhcXG4nLCAnICAgIHBhdGgud3JpdGVfdGV4dCgiXFxcXG4iLmpvaW4obGluZXMpICsgIlxcXFxuIiwgZW5jb2Rpbmc9InV0Zi04IilcXG4gICAgTEFURVNUX0NPTU1BTkRfUE9JTlRFUi53cml0ZV90ZXh0KHBhdGguYXNfcG9zaXgoKSArICJcXFxuIiwgZW5jb2Rpbmc9InV0Zi04IilcXG4gICAgcmV0dXJuIHBhdGhcXG4nKQppZiAndXBsb2FkX3BhdGhzID0gW3JlcG9ydCwgTEFURVNUX0NPTU1BTkRfUE9JTlRFUiwgRVhFQ1VURURfSlNPTkwsICpleHRyYV91cGxvYWRfcGF0aHNdJyBub3QgaW4gdGV4dDoKICAgIHRleHQgPSB0ZXh0LnJlcGxhY2UoJyAgICB1cGxvYWRfcGF0aHMgPSBbcmVwb3J0LCBFWEVDVVRFRF9KU09OTCwgKmV4dHJhX3VwbG9hZF9wYXRoc11cXG4nLCAnICAgIHVwbG9hZF9wYXRocyA9IFtyZXBvcnQsIExBVEVTVF9DT01NQU5EX1BPSU5URVIsIEVYRUNVVEVEX0pTT05MLCAqZXh0cmFfdXBsb2FkX3BhdGhzXVxcbicpCnJ1bm5lci53cml0ZV90ZXh0KHRleHQsIGVuY29kaW5nPSJ1dGYtOCIpCgp0ZXN0X3BhdGggPSBQYXRoKCJ0ZXN0cy90ZXN0X2FnZW50X2NvbW1hbmRfcnVubmVyLnB5IikKdGVzdCA9IHRlc3RfcGF0aC5yZWFkX3RleHQoZW5jb2Rpbmc9InV0Zi04IikKaWYgInRlc3Rfd3JpdGVfcmVwb3J0X3VwZGF0ZXNfbGF0ZXN0X2NvbW1hbmRfcG9pbnRlciIgbm90IGluIHRlc3Q6CiAgICB0ZXN0ICs9ICdccblxuZGVmIHRlc3Rfd3JpdGVfcmVwb3J0X3VwZGF0ZXNfbGF0ZXN0X2NvbW1hbmRfcG9pbnRlcih0bXBfcGF0aCwgbW9ua2V5cGF0Y2gpOlxuICAgIG1vbmtleXBhdGNoLmNoZGlyKHRtcF9wYXRoKVxuICAgIHdyaXRlX2NvbW1hbmQodG1wX3BhdGgsIGNvbW1hbmRfaWQ9ImNtZC1wb2ludGVyIilcbiAgICBjb21tYW5kID0gYWNyLmxvYWRfY3VycmVudF9jb21tYW5kKClcbiAgICByZXBvcnQgPSBhY3Iud3JpdGVfcmVwb3J0KGNvbW1hbmQsIGFjci5PVVRDT01FX1BBU1NfRVhFQ1VURUQsIDAsIFBhdGgoImRvY3MvcmVwb3J0cy90ZXJtaW5hbC9jbWQtcG9pbnRlci5sb2ciKSlcbiAgICBhc3NlcnQgYWNyLkxBVEVTVF9DT01NQU5EX1BPSU5URVIuZXhpc3RzKClcbiAgICBhc3NlcnQgYWNyLkxBVEVTVF9DT01NQU5EX1BPSU5URVIucmVhZF90ZXh0KGVuY29kaW5nPSJ1dGYtOCIpLnN0cmlwKCkgPT0gcmVwb3J0LmFzX3Bvc2l4KClcblxuXG5kZWYgdGVzdF9hZ2VudF9ydW5fdXBsb2Fkc19sYXRlc3RfY29tbWFuZF9wb2ludGVyKHRtcF9wYXRoLCBtb25rZXlwYXRjaCk6XG4gICAgbW9ua2V5cGF0Y2guY2hkaXIodG1wX3BhdGgpXG4gICAgd3JpdGVfY29tbWFuZCh0bXBfcGF0aCwgY29tbWFuZF9pZD0iY21kLXVwbG9hZC1wb2ludGVyIilcbiAgICBsb2dfcGF0aCA9IFBhdGgoImRvY3MvcmVwb3J0cy90ZXJtaW5hbC9jbWQtdXBsb2FkLXBvaW50ZXIubG9nIilcbiAgICBsb2dfcGF0aC5wYXJlbnQubWtkaXIocGFyZW50cz1UcnVlKVxuICAgIGxvZ19wYXRoLndyaXRlX3RleHQoImxvZyIgKyBjaHIoMTApLCBlbmNvZGluZz0idXRmLTgiKVxuICAgIG1vbmtleXBhdGNoLnNldGF0dHIoYWNyLnRlcm1pbmFsX2xvZ2dpbmcsICJydW5fbG9nZ2VkIiwgbGFtYmRhIG5hbWUsIGNvbW1hbmQ6IDApXG4gICAgbW9ua2V5cGF0Y2guc2V0YXR0cihhY3IudGVybWluYWxfbG9nZ2luZywgInJlYWRfbGF0ZXN0X3BvaW50ZXIiLCBsYW1iZGE6IGxvZ19wYXRoKVxuICAgIHB1c2hlZF9wYXRocyA9IFtdXG4gICAgZGVmIGZha2Vfc3RhZ2VfY29tbWl0X3B1c2gocGF0aHMsIG1lc3NhZ2UpOlxuICAgICAgICBwdXNoZWRfcGF0aHMuZXh0ZW5kKHBhdGguYXNfcG9zaXgoKSBmb3IgcGF0aCBpbiBwYXRocylcbiAgICAgICAgcmV0dXJuIDBcbiAgICBtb25rZXlwYXRjaC5zZXRhdHRyKGFjciwgInN0YWdlX2NvbW1pdF9wdXNoIiwgZmFrZV9zdGFnZV9jb21taXRfcHVzaClcbiAgICBhc3NlcnQgYWNyLmFnZW50X3J1bigpID09IDBcbiAgICBhc3NlcnQgImRvY3MvcmVwb3J0cy9jb21tYW5kX3J1bnMvTEFURVNUX0NPTU1BTkRfUlVOLnR4dCIgaW4gcHVzaGVkX3BhdGhzXG4nCnRlc3RfcGF0aC53cml0ZV90ZXh0KHRlc3QsIGVuY29kaW5nPSJ1dGYtOCIpCgpyZXBvX3J1bm5lciA9IFBhdGgoImRvY3Mvd29ya2Zsb3cvUkVQT19DT01NQU5EX1JVTk5FUi5tZCIpCnJlcG9fdGV4dCA9IHJlcG9fcnVubmVyLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgiKQppZiAiIyMgUmVzdWx0IGhhbmRvZmYgcG9pbnRlciIgbm90IGluIHJlcG9fdGV4dDoKICAgIHJlcG9fdGV4dCA9IHJlcG9fdGV4dC5yc3RyaXAoKSArICJcXG5cXG4iICsgJyMjIFJlc3VsdCBoYW5kb2ZmIHBvaW50ZXJcblxuRXZlcnkgYWdlbnQgY29tbWFuZCBydW4gd3JpdGVzIGEgbWFjaGluZS1yZWFkYWJsZSBsYXRlc3QtcmVwb3J0IHBvaW50ZXIgYXQgYGRvY3MvcmVwb3J0cy9jb21tYW5kX3J1bnMvTEFURVNUX0NPTU1BTkRfUlVOLnR4dGAuIFRoZSBwb2ludGVyIHJlZmVyZW5jZXMgdGhlIG5ld2VzdCBgZG9jcy9yZXBvcnRzL2NvbW1hbmRfcnVucy8qLm1kYCByZXBvcnQsIGFuZCB0aGF0IHJlcG9ydCByZWZlcmVuY2VzIHRoZSB0ZXJtaW5hbCBsb2cuIFRoaXMgaXMgdGhlIG5vcm1hbCBgZGAvYGZgIGhhbmRvZmYgcGF0aDogYWZ0ZXIgYC4vbnMgYWdlbnQtbmV4dGAsIHRoZSB1c2VyIGNhbiBhbnN3ZXIgb25seSBgZGAgZm9yIFBBU1Mgb3IgYGZgIGZvciBub3JtYWwgRkFJTCwgYW5kIHRoZSBuZXh0IGFnZW50IHJlYWRzIHRoZSBjb21taXR0ZWQgcG9pbnRlci9yZXBvcnQvbG9nIGZyb20gdGhlIHJlbW90ZSByZXBvc2l0b3J5LiBDb3B5LWFuZC1wYXN0ZSBpcyByZXNlcnZlZCBmb3IgdGVybWluYWwgY3Jhc2hlcywuLi4nICsgIlxcbiIKcmVwb19ydW5uZXIud3JpdGVfdGV4dChyZXBvX3RleHQsIGVuY29kaW5nPSJ1dGYtOCIpCgpldmlkZW5jZSA9IFBhdGgoImRvY3Mvd29ya2Zsb3cvTk9fQ09QWV9URVJNSU5BTF9FVklERU5DRS5tZCIpCmV2X3RleHQgPSBldmlkZW5jZS5yZWFkX3RleHQoZW5jb2Rpbmc9InV0Zi04IikKaWYgIiMjIGBkYC9gZmAgYWdlbnQtcmVzdWx0IGhhbmRvZmYiIG5vdCBpbiBldl90ZXh0OgogICAgZXZfdGV4dCA9IGV2X3RleHQucnN0cmlwKCkgKyAiXFxuXFxuIiArICcjIyBgZGAvYGZgIGFnZW50LXJlc3VsdCBoYW5kb2ZmXG5cbkZvciByZXBvLWJhY2tlZCBhZ2VudCBjb21tYW5kcywgYGRvY3MvcmVwb3J0cy9jb21tYW5kX3J1bnMvTEFURVNUX0NPTU1BTkRfUlVOLnR4dGAgaXMgdGhlIGZpcnN0IGZpbGUgdG8gcmVhZCBhZnRlciB0aGUgdXNlciByZXBsaWVzIGBkYCBvciBgZmAuIFRoZSByZWZlcmVuY2VkIGNvbW1hbmQgcmVwb3J0IGNvbnRhaW5zIHRoZSBvdXRjb21lLCBleGl0IGNvZGUsIGJyYW5jaCwgc2NyaXB0IGhhc2gsIGFuZCB0ZXJtaW5hbC1sb2cgcGF0aC4gQSBub3JtYWwgRkFJTCBtdXN0IHN0aWxsIGJlIHB1c2hlZCB0byB0aGUgcmVtb3RlIHJlcG9zaXRvcnksIHNvIGBmYCBzaG91bGQgYmUgZW5vdWdoIHVubGVzcyB0aGUgdGVybWluYWwgY3Jhc2hlZCwgYXV0aGVudGljYXRpb24vbmV0d29yayBhY2Nlc3MgZmFpbGVkLCBvciBubyByZW1vdGUgZXZpZGVuY2Ugd2FzIHByb2R1Y2VkLicgKyAiXFxuIgpldmlkZW5jZS53cml0ZV90ZXh0KGV2X3RleHQsIGVuY29kaW5nPSJ1dGYtOCIpCgpnYXRlcyA9IFBhdGgoImRvY3MvVEVTVF9HQVRFUy5tZCIpCmdhdGVzX3RleHQgPSBnYXRlcy5yZWFkX3RleHQoZW5jb2Rpbmc9InV0Zi04IikKaWYgIiMjIE5vLWNvcHkgYWdlbnQgcmVzdWx0IGhhbmRvZmYiIG5vdCBpbiBnYXRlc190ZXh0OgogICAgZ2F0ZXNfdGV4dCA9IGdhdGVzX3RleHQucnN0cmlwKCkgKyAiXFxuXFxuIiArICcjIyBOby1jb3B5IGFnZW50IHJlc3VsdCBoYW5kb2ZmXG5cbmB0ZXN0cy90ZXN0X2FnZW50X2NvbW1hbmRfcnVubmVyLnB5YCB2ZXJpZmllcyB0aGF0IGBhZ2VudC1ydW5gIHdyaXRlcyBhbmQgdXBsb2FkcyBgZG9jcy9yZXBvcnRzL2NvbW1hbmRfcnVucy9MQVRFU1RfQ09NTUFORF9SVU4udHh0YC4gVGhpcyBwb2ludGVyIGlzIHRoZSBtYWNoaW5lLXJlYWRhYmxlIGJyaWRnZSBmcm9tIGEgdXNlciByZXBseSBvZiBgZGAgb3IgYGZgIHRvIHRoZSBjb21taXR0ZWQgY29tbWFuZCByZXBvcnQgYW5kIHRlcm1pbmFsIGxvZy4gVGhlIGNvbnRyYWN0IGlzOiBub3JtYWwgUEFTUyBhbmQgbm9ybWFsIEZBSUwgYm90aCBsZWF2ZSByZW1vdGUgZXZpZGVuY2U7IGNvcHktYW5kLXBhc3RlIGlzIG9ubHkgYWNjZXB0YWJsZSBmb3IgdGVybWluYWwgY3Jhc2gsIGF1dGhlbnRpY2F0aW9uL25ldHdvcmsgZmFpbHVyZSwgb3IgbWlzc2luZyByZW1vdGUgZXZpZGVuY2UuJyArICJcXG4iCmdhdGVzLndyaXRlX3RleHQoZ2F0ZXNfdGV4dCwgZW5jb2Rpbmc9InV0Zi04IikK' | base64 -d > /tmp/no_copy_result_handoff_pointer_patch.py || OK=1

printf '\n### RUN PATCH SCRIPT ###\n'
PY='.venv/bin/python'
if [ ! -x "$PY" ]
then
  PY='python3'
fi
$PY /tmp/no_copy_result_handoff_pointer_patch.py || OK=1

printf '\n### VERIFY PATCH CONTENT ###\n'
grep -R 'LATEST_COMMAND_RUN.txt\|Result handoff pointer\|agent-result handoff\|No-copy agent result handoff' -n src/agentic_project_kit/agent_command_runner.py tests/test_agent_command_runner.py docs/workflow/REPO_COMMAND_RUNNER.md docs/workflow/NO_COPY_TERMINAL_EVIDENCE.md docs/TEST_GATES.md || OK=1

printf '\n### LOCAL GATES ###\n'
$PY -m pytest -q tests/test_agent_command_runner.py || OK=1
./ns terminal-remote-preflight || OK=1
./ns state-freshness-check || OK=1
./ns artifact-gc || OK=1
./ns handoff-check || OK=1
./ns governance-check || OK=1
./ns dev || OK=1

printf '\n### COMMIT PATCH ###\n'
git status --short || OK=1
git add src/agentic_project_kit/agent_command_runner.py tests/test_agent_command_runner.py docs/workflow/REPO_COMMAND_RUNNER.md docs/workflow/NO_COPY_TERMINAL_EVIDENCE.md docs/TEST_GATES.md || OK=1
if git diff --cached --quiet
then
  printf 'NO_PATCH_TO_COMMIT\n'
else
  git commit -m 'Add no-copy agent result handoff pointer' || OK=1
fi

printf '\n### PUSH PATCH BRANCH ###\n'
git push -u origin $BRANCH || OK=1

printf '\n### CREATE OR SHOW PR ###\n'
gh pr create --title 'Add no-copy agent result handoff pointer' --body 'Adds a committed latest command-run pointer so d/f handoff can be resolved from remote command-run evidence without terminal copy-and-paste.' --base main --head $BRANCH || gh pr view $BRANCH --json number,title,state,url || OK=1

printf '\n### FINAL STATE BEFORE AGENT REPORT UPLOAD ###\n'
git branch --show-current
git status --short

if [ "$OK" -eq 0 ]
then
  printf '\n### RESULT: PASS ###\n'
else
  printf '\n### RESULT: FAIL ###\n'
fi
exit $OK
