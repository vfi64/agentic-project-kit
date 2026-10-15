"""Build tracer targets: code locations (file:co_firstlineno) of CLI callbacks and single-owner core functions.

Usage: <kit-python> build_targets.py <callbacks.json> <result.json> <out_targets.json>
"""
import importlib
import inspect
import json
import sys


def rel(path):
    i = path.rfind("/agentic_project_kit/")
    return path[i + 1:] if i >= 0 else path

cbs = json.load(open(sys.argv[1]))
res = json.load(open(sys.argv[2]))
out = {"callbacks": {}, "core": {}}
for cmd, info in cbs.items():
    if info and info.get("file"):
        out["callbacks"][f"{rel(info['file'])}:{info['line']}"] = cmd
skipped = 0
for fid, cmd in res["core_owner"].items():
    mod, qn = fid.split(":", 1)
    if "<locals>" in qn:
        skipped += 1
        continue
    try:
        obj = importlib.import_module(mod)
        for part in qn.split("."):
            obj = getattr(obj, part)
        fn = inspect.unwrap(obj)
        code = fn.__code__
        out["core"][f"{rel(code.co_filename)}:{code.co_firstlineno}"] = cmd
    except Exception:
        skipped += 1
json.dump(out, open(sys.argv[3], "w"), indent=1)
print("callbacks", len(out["callbacks"]), "core", len(out["core"]), "skipped", skipped)
