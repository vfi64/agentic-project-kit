from __future__ import annotations

import subprocess
from pathlib import Path


def test_zero_ns_shell_adapter_contract_is_now_zero_ns() -> None:
    assert not Path("ns").exists()
    assert not Path("ns-menu").exists()
    assert subprocess.check_output(["git", "ls-files", "*.sh"], text=True).strip() == ""
