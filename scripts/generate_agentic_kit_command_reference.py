from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click
from typer.main import get_command

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

REFERENCE_JSON = ROOT / "docs/reference/agentic-kit-commands.json"
REFERENCE_MD = ROOT / "docs/reference/AGENTIC_KIT_COMMANDS.md"


def _param_type(param: click.Parameter