"""Managed consumer CI; ambiguity selects the existing full audit suite."""

from __future__ import annotations


def render_workspace_ci(version: str) -> str:
    return """name: Agentic Gate

"on":
  pull_request:
  push:
    branches:
      - main

permissions:
  contents: read

concurrency:
  group: agentic-gate-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

jobs:
  agentic-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"
      - uses: actions/cache@v4
        with:
          path: ~/.cache/ms-playwright
          key: ${{ runner.os }}-ms-playwright-${{ hashFiles('**/pyproject.toml', '**/package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-ms-playwright-
      - run: python -m pip install --upgrade pip
      - run: python -m pip install agentic-project-kit==__KIT_VERSION__
      - name: Classify workspace refresh
        id: ci-policy
        shell: bash
        env:
          EVENT_NAME: ${{ github.event_name }}
          REFRESH_BRANCH: ${{ github.head_ref }}
          BASE_SHA: ${{ github.event.pull_request.base.sha }}
          HEAD_SHA: ${{ github.event.pull_request.head.sha }}
        run: |
          paths="$RUNNER_TEMP/agentic-changed-paths"
          decision="$RUNNER_TEMP/agentic-ci-policy.json"
          : > "$paths"
          if [[ "$EVENT_NAME" == pull_request && "$BASE_SHA" =~ ^[a-f0-9]{40}$ && "$HEAD_SHA" =~ ^[a-f0-9]{40}$ ]]; then
            if git fetch --no-tags origin "$BASE_SHA" "$HEAD_SHA" && git diff --no-renames --name-only -z "$BASE_SHA" "$HEAD_SHA" > "$paths"; then
              :
            else
              : > "$paths"
            fi
          fi
          python -m agentic_project_kit.ci_runtime_policy workspace-refresh --root . --changed-paths-file "$paths" --branch "$REFRESH_BRANCH" --event-name "$EVENT_NAME" --output "$decision"
          python -c 'import json, os; from pathlib import Path; mode = json.loads(Path(os.environ["RUNNER_TEMP"], "agentic-ci-policy.json").read_text())["mode"]; print("mode=" + mode)' >> "$GITHUB_OUTPUT"
      - name: Check workspace refresh
        if: steps.ci-policy.outputs.mode == 'ADMIN_REFRESH_LIGHT'
        run: agentic-kit check --root . --json
      - name: Full workspace audit suite
        if: steps.ci-policy.outputs.mode != 'ADMIN_REFRESH_LIGHT'
        run: agentic-kit standard-gates-audit-suite
""".replace("__KIT_VERSION__", version)
