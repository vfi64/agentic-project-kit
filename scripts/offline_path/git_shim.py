#!/usr/bin/env python3
"""Simulation shim: report the configured (un-rewritten) origin URL; delegate everything else to the real git."""
import os
import shutil
import sys

here = os.path.dirname(os.path.abspath(__file__))
path = os.pathsep.join(p for p in os.environ.get("PATH", "").split(os.pathsep) if os.path.abspath(p) != here)
real = shutil.which("git", path=path)
args = sys.argv[1:]
if " remote get-url origin " in " " + " ".join(args) + " ":
    args = args[: args.index("remote")] + ["config", "--get", "remote.origin.url"]
os.execv(real, [real, *args])
