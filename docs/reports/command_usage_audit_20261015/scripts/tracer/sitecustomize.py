"""Runtime tracer for agentic-kit command usage (loaded via PYTHONPATH when KIT_TRACE_LOG is set).

Records, per process, every entry into
  * a CLI callback of one of the manifest commands, and
  * a "core" function that the static analysis attributed to exactly one command,
together with the active ancestry: the in-process stack of traced commands plus the
ancestry inherited from the parent process (env KIT_TRACE_PARENT).

Targets file (JSON): {"callbacks": {"<file>:<firstlineno>": "<command>"}, "core": {...}}
"""
import json
import os
import sys
import threading

_LOG = os.environ.get("KIT_TRACE_LOG")
_TARGETS = os.environ.get("KIT_TRACE_TARGETS")

if _LOG and _TARGETS:
    try:
        _t = json.load(open(_TARGETS))
        _CB = _t["callbacks"]
        _CORE = _t["core"]
    except Exception:
        _CB, _CORE = {}, {}
    _PARENT = [x for x in os.environ.get("KIT_TRACE_PARENT", "").split("|") if x]
    _stack = []
    _lock = threading.Lock()
    _test = {"id": ""}
    _MARK = "/agentic_project_kit/"
    _norm_cache = {}

    def _norm(fn):
        r = _norm_cache.get(fn)
        if r is None:
            i = fn.rfind(_MARK)
            r = fn[i + 1:] if i >= 0 else ""
            _norm_cache[fn] = r
        return r

    _files = {k.rsplit(":", 1)[0] for k in list(_CB) + list(_CORE)}

    def _emit(kind, cmd):
        rec = {
            "pid": os.getpid(),
            "kind": kind,
            "command": cmd,
            "ancestry": _PARENT + [c for c in _stack],
            "test": os.environ.get("PYTEST_CURRENT_TEST", "").split(" ")[0],
            "argv0": " ".join(sys.argv[:4])[:200],
            "scenario": os.environ.get("SIM_SCENARIO", ""),
            "step": os.environ.get("SIM_STEP", ""),
        }
        with _lock:
            with open(_LOG, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")

    def _prof(frame, event, arg):
        if event not in ("call", "return"):
            return
        co = frame.f_code
        fn = _norm(co.co_filename)
        if fn not in _files:
            return
        key = f"{fn}:{co.co_firstlineno}"
        cmd = _CB.get(key)
        kind = "cli"
        if cmd is None:
            cmd = _CORE.get(key)
            kind = "core"
        if cmd is None:
            return
        if event == "call":
            if kind == "core" and (cmd in _stack):
                return  # a command calling its own core function
            _emit(kind, cmd)
            if kind == "cli":
                _stack.append(cmd)
                os.environ["KIT_TRACE_PARENT"] = "|".join(_PARENT + _stack)
        elif kind == "cli" and _stack and _stack[-1] == cmd:
            _stack.pop()
            os.environ["KIT_TRACE_PARENT"] = "|".join(_PARENT + _stack)

    sys.setprofile(_prof)
    threading.setprofile(_prof)
