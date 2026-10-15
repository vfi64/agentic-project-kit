"""Extract recorded agentic-kit invocations from evidence text (JSON, logs, Markdown).

Classes per hit:
  executed   - JSON step with argv + returncode, or a shell-trace line ("$ ... agentic-kit ...")
  argv_only  - JSON argv list without a result (planned / described step)
  mention    - inline prose mention "agentic-kit x y"

Library usage: extract(text, name) -> list[(cls, qualified_name_or_legacy, detail)]
CLI usage:     python extract_traces.py <repo_root> <file>...   (prints JSON lines)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ENTRY_RE = re.compile(r"(?:^|[\s/\"'`(])agentic-kit((?:\s+[a-z][a-z0-9_-]*){1,3})")
SHELL_RE = re.compile(r"^\s*(?:\$|\+|>|RUN:?|CMD:?|COMMAND=)\s*(?:\S*/)?agentic-kit((?:\s+[a-z][a-z0-9_-]*){1,3})", re.M)
MODULE_TOKENS = {"agentic_project_kit.cli", "agentic_project_kit"}


class Matcher:
    def __init__(self, manifest_path: Path):
        cmds = json.load(open(manifest_path))["commands"]
        self.paths = {tuple(c["path"]): c["qualified_name"] for c in cmds}
        self.groups = {c["path"][0] for c in cmds if len(c["path"]) > 1}
        self.max_len = max(len(p) for p in self.paths)

    def match(self, toks: list[str]) -> str | None:
        toks = [t for t in toks if t]
        for L in range(min(self.max_len, len(toks)), 0, -1):
            if tuple(toks[:L]) in self.paths:
                return self.paths[tuple(toks[:L])]
        if toks:
            # unknown command: keep as legacy name (group + sub if group-like)
            if toks[0] in self.groups and len(toks) > 1:
                return "LEGACY agentic-kit " + " ".join(toks[:2])
            return "LEGACY agentic-kit " + toks[0]
        return None


def _argv_tokens(lst):
    if not lst or not all(isinstance(x, str) for x in lst[: min(len(lst), 4)]):
        return None
    for i, v in enumerate(lst):
        if not isinstance(v, str):
            return None
        if v.endswith("agentic-kit") or v in MODULE_TOKENS:
            if v in MODULE_TOKENS and (i == 0 or lst[i - 1] != "-m"):
                continue
            toks = []
            for w in lst[i + 1 :]:
                if not isinstance(w, str) or w.startswith("-") or not re.fullmatch(r"[a-z][a-z0-9_-]*", w):
                    break
                toks.append(w)
            return toks
        if i > 2:
            return None
    return None


def _walk_json(obj, m: Matcher, out, parent=None):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, list):
                toks = _argv_tokens(v)
                if toks is not None:
                    q = m.match(toks)
                    if q:
                        executed = "returncode" in obj or "exit_code" in obj or "rc" in obj
                        out.append(("executed" if executed else "argv_only", q, k))
                        continue
            _walk_json(v, m, out, obj)
    elif isinstance(obj, list):
        toks = _argv_tokens(obj)
        if toks is not None and parent is None:
            q = m.match(toks)
            if q:
                out.append(("argv_only", q, "list"))
                return
        for v in obj:
            _walk_json(v, m, out, obj)
    elif isinstance(obj, str) and "agentic-kit" in obj and len(obj) < 2_000_000:
        for seg in _json_segments(obj):
            _walk_json(seg, m, out)
        for mm in SHELL_RE.finditer(obj):
            q = m.match(mm.group(1).split())
            if q:
                out.append(("executed", q, "json-embedded-trace"))


_DEC = json.JSONDecoder()


def _json_segments(text: str):
    """Yield JSON documents embedded in text (whole text, or objects starting a line)."""
    s = text.strip()
    if s[:1] in "{[":
        try:
            yield json.loads(s)
            return
        except Exception:
            pass
    pos = 0
    n = len(text)
    while pos < n:
        i = text.find("\n{", pos)
        start = 0 if pos == 0 and text.startswith("{") else (i + 1 if i >= 0 else -1)
        if start < 0:
            break
        try:
            obj, end = _DEC.raw_decode(text, start)
            yield obj
            pos = end
        except Exception:
            pos = start + 1


def extract(text: str, name: str, m: Matcher):
    out = []
    segs = list(_json_segments(text)) if "agentic-kit" in text or "agentic_project_kit" in text else []
    for seg in segs:
        _walk_json(seg, m, out)
    if segs and text.strip()[:1] in "{[":
        return out
    traced_spans = []
    for mm in SHELL_RE.finditer(text):
        q = m.match(mm.group(1).split())
        if q:
            out.append(("executed", q, "shell-trace"))
            traced_spans.append(mm.span())
    for mm in ENTRY_RE.finditer(text):
        if any(a <= mm.start() < b for a, b in traced_spans):
            continue
        q = m.match(mm.group(1).split())
        if q:
            out.append(("mention", q, "prose"))
    return out


if __name__ == "__main__":
    root = Path(sys.argv[1])
    mt = Matcher(root / "docs/reference/agentic-kit-commands.json")
    for f in sys.argv[2:]:
        p = Path(f)
        try:
            t = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for cls, q, d in extract(t, p.name, mt):
            print(json.dumps({"file": f, "class": cls, "command": q, "detail": d}))
