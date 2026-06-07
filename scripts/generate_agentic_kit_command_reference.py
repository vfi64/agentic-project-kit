from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click
from typer.main import get_command

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

REFERENCE_JSON = ROOT / "docs/reference/agentic-kit-commands.json"
REFERENCE