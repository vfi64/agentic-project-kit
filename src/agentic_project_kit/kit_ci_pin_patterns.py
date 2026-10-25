"""One stable exact-pin expression for CI planning and downgrade checks."""
from __future__ import annotations

import re

EXACT_KIT_PIN_EXPRESSION = r"agentic-project-kit==([0-9]+\.[0-9]+\.[0-9]+)(?![\w.+!*-])"
EXACT_KIT_PIN = re.compile(EXACT_KIT_PIN_EXPRESSION, re.ASCII)
EXACT_KIT_PIN_BYTES = re.compile(EXACT_KIT_PIN_EXPRESSION.encode("ascii"))
