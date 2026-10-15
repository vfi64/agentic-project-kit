"""Static analysis: which Kit commands are used by the 34 orchestrator commands.

Two channels:
  A  subprocess invocation: argv literals that name a manifest command path
     (["agentic-kit", ...], [..., "-m", "agentic_project_kit.cli", ...], or calls to
     argv helper functions such as _agentic("transfer", "commit")).
  B  in-process call: the orchestrator's static call graph reaches another
     command's CLI callback, or a "core" function owned exclusively by that callback.

Usage: python analyze.py <repo_root> <callbacks.json> <out.json>
"""
from __future__ import annotations

import ast
import json
import sys
from collections import defaultdict
from pathlib import Path

repo = Path(sys.argv[1])
callbacks = json.load(open(sys.argv[2]))
out_path = sys.argv[3]
pkg_root = repo / "src"
manifest = json.load(open(repo / "docs/reference/agentic-kit-commands.json"))["commands"]
by_name = {c["qualified_name"]: c for c in manifest}
paths = {tuple(c["path"]): c["qualified_name"] for c in manifest}
max_len = max(len(p) for p in paths)
KIT_MARKERS = {"agentic-kit", "agentic_project_kit.cli", "agentic_project_kit"}
KIT_RESOLVERS = {"default_agentic_kit", "owned_agentic_kit", "current_agentic_kit", "_agentic_kit_command", "_agentic_kit_executable"}
KIT_SENTINEL = "\x00KIT"

# ---------------------------------------------------------------- module index
modules: dict[str, Path] = {}
for f in pkg_root.rglob("*.py"):
    rel = f.relative_to(pkg_root).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    modules[".".join(parts)] = f


def resolve_relative(mod: str, level: int, target: str | None, is_pkg: bool) -> str:
    base = mod.split(".")
    if not is_pkg:
        base = base[:-1]
    if level > 1:
        base = base[: len(base) - (level - 1)]
    return ".".join(base + ([target] if target else []))


# function id = "module:qualname"
func_nodes: dict[str, ast.AST] = {}
func_module: dict[str, str] = {}
func_scope_imports: dict[str, dict[str, str]] = {}  # per function: local import aliases
module_imports: dict[str, dict[str, str]] = {}  # alias -> "mod" or "mod:name"
module_defs: dict[str, dict[str, str]] = defaultdict(dict)  # top-level name -> fid
class_methods: dict[str, dict[str, str]] = defaultdict(dict)  # "mod:Class" -> {meth: fid}
local_defs: dict[str, dict[str, str]] = defaultdict(dict)  # enclosing fid -> {name: fid}


def collect_imports(body_nodes, mod, is_pkg) -> dict[str, str]:
    imp = {}
    for node in body_nodes:
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.asname:
                    imp[a.asname] = a.name
                else:
                    imp[a.name.split(".")[0]] = a.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                src = resolve_relative(mod, node.level, node.module, is_pkg)
            else:
                src = node.module or ""
            for a in node.names:
                if a.name == "*":
                    imp.setdefault("*", "")
                    imp["*"] = (imp["*"] + "|" + src).strip("|")
                    continue
                name = a.asname or a.name
                sub = f"{src}.{a.name}"
                imp[name] = sub if sub in modules else f"{src}:{a.name}"
    return imp


def own_imports(fn_node, mod, is_pkg):
    """Imports anywhere inside a function body (not inside nested defs)."""
    found = []
    stack = list(fn_node.body)
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            found.append(n)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        else:
            stack.extend(ast.iter_child_nodes(n))
    return collect_imports(found, mod, is_pkg)


def visit_defs(body, mod, prefix, enclosing_fid, cls, is_pkg):
    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            qn = f"{prefix}{node.name}"
            fid = f"{mod}:{qn}"
            func_nodes[fid] = node
            func_module[fid] = mod
            func_scope_imports[fid] = own_imports(node, mod, is_pkg)
            if cls:
                class_methods[f"{mod}:{cls}"][node.name] = fid
            elif enclosing_fid:
                local_defs[enclosing_fid][node.name] = fid
            else:
                module_defs[mod][node.name] = fid
            visit_defs(node.body, mod, f"{qn}.<locals>.", fid, None, is_pkg)
        elif isinstance(node, ast.ClassDef):
            qn = f"{prefix}{node.name}"
            if not cls and not enclosing_fid:
                module_defs[mod][node.name] = f"{mod}:{qn}"  # class; calls -> __init__
            visit_defs(node.body, mod, f"{qn}.", enclosing_fid, qn, is_pkg)
        elif isinstance(node, (ast.If, ast.Try, ast.With)):
            for fld in ("body", "orelse", "finalbody", "handlers"):
                sub = getattr(node, fld, None)
                if sub:
                    inner = []
                    for s in sub:
                        inner.extend(s.body if isinstance(s, ast.ExceptHandler) else [s])
                    visit_defs(inner, mod, prefix, enclosing_fid, cls, is_pkg)


for mod, f in modules.items():
    tree = ast.parse(f.read_text(encoding="utf-8"))
    is_pkg = f.name == "__init__.py"
    module_imports[mod] = collect_imports(tree.body, mod, is_pkg)
    visit_defs(tree.body, mod, "", None, None, is_pkg)


def module_name_target(mod: str, name: str, depth: int = 0) -> str | None:
    """Return 'mod:name' (definition site) or import target for name visible in mod."""
    if depth > 8:
        return None
    if name in module_defs.get(mod, {}):
        return f"{mod}:{name}"
    imp = module_imports.get(mod, {})
    if name in imp and name != "*":
        return imp[name]
    for src in filter(None, imp.get("*", "").split("|")):
        t = module_name_target(src, name, depth + 1)
        if t:
            return t
    return None


def lookup_symbol(target: str) -> str | None:
    """'mod:name' or 'mod' -> fid (functions only; classes map to __init__)."""
    if ":" not in target:
        return None
    mod, name = target.split(":", 1)
    # follow re-exports
    for _ in range(5):
        if name in module_defs.get(mod, {}):
            fid = module_defs[mod][name]
            if fid in func_nodes:
                return fid
            init = class_methods.get(fid, {}).get("__init__")
            return init or None
        nxt = module_name_target(mod, name)
        if not nxt or ":" not in nxt or nxt == f"{mod}:{name}":
            return None
        mod, name = nxt.split(":", 1)
    return None


def lookup_class(target: str) -> str | None:
    if not target or ":" not in target:
        return None
    mod, name = target.split(":", 1)
    for _ in range(8):
        if name in module_defs.get(mod, {}):
            key = module_defs[mod][name]
            return key if key in class_methods else None
        nxt = module_name_target(mod, name)
        if not nxt or ":" not in nxt or nxt == f"{mod}:{name}":
            return None
        mod, name = nxt.split(":", 1)
    return None


def class_of_name(fid, name) -> str | None:
    mod = func_module[fid]
    for scope in enclosing_chain(fid):
        imp = func_scope_imports.get(scope, {}).get(name)
        if imp:
            return lookup_class(imp)
    t = module_name_target(mod, name)
    return lookup_class(t) if t else None


LOCAL_INSTANCES: dict[str, str] = {}


def enclosing_chain(fid):
    """fid and its enclosing function fids (for closures)."""
    chain = [fid]
    mod, qn = fid.split(":", 1)
    while ".<locals>." in qn:
        qn = qn.rsplit(".<locals>.", 1)[0]
        chain.append(f"{mod}:{qn}")
    return chain


def resolve_call(fid, func_expr) -> str | None:
    mod = func_module[fid]
    if isinstance(func_expr, ast.Name):
        name = func_expr.id
        for scope in enclosing_chain(fid):
            if name in local_defs.get(scope, {}):
                return local_defs[scope][name]
            imp = func_scope_imports.get(scope, {}).get(name)
            if imp:
                return lookup_symbol(imp)
        t = module_name_target(mod, name)
        if t:
            return lookup_symbol(t) if ":" in t else None
        return None
    if isinstance(func_expr, ast.Attribute) and isinstance(func_expr.value, ast.Call) and isinstance(func_expr.value.func, ast.Name):
        ck = class_of_name(fid, func_expr.value.func.id)
        if ck:
            return class_methods.get(ck, {}).get(func_expr.attr)
        return None
    if isinstance(func_expr, ast.Attribute) and isinstance(func_expr.value, ast.Name) and func_expr.value.id in LOCAL_INSTANCES:
        return class_methods.get(LOCAL_INSTANCES[func_expr.value.id], {}).get(func_expr.attr)
    if isinstance(func_expr, ast.Attribute) and isinstance(func_expr.value, ast.Name):
        base, attr = func_expr.value.id, func_expr.attr
        if base in ("self", "cls"):
            qn = fid.split(":", 1)[1]
            cls = qn.rsplit(".", 1)[0] if "." in qn else None
            if cls:
                return class_methods.get(f"{mod}:{cls}", {}).get(attr)
            return None
        target = None
        for scope in enclosing_chain(fid):
            target = func_scope_imports.get(scope, {}).get(base) or target
        target = target or module_name_target(mod, base)
        if target and ":" not in target and target in modules:
            return lookup_symbol(f"{target}:{attr}")
    return None


# ---------------------------------------------------------------- argv helpers
KIT_NAMES: set[str] = set()  # dynamic, per analysed function (local vars + self attrs)


def str_const(n):
    if isinstance(n, ast.Constant) and isinstance(n.value, str):
        return n.value
    if isinstance(n, ast.Name) and n.id in KIT_NAMES:
        return KIT_SENTINEL
    if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "self" and f"self.{n.attr}" in KIT_NAMES:
        return KIT_SENTINEL
    if isinstance(n, ast.Attribute) and n.attr in globals().get("KIT_ATTR_NAMES", ()):
        return KIT_SENTINEL
    if isinstance(n, ast.Call):
        f = n.func
        name = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
        if name in KIT_RESOLVERS:
            return KIT_SENTINEL
    if isinstance(n, ast.Starred) and isinstance(n.value, ast.Name) and n.value.id.isupper():
        return KIT_SENTINEL if "KIT" in n.value.id or "AGENTIC" in n.value.id else None
    return None


def is_argv_helper(node) -> bool:
    """A function that prepends a Kit entrypoint to *parts."""
    has_marker = False
    has_star = node.args.vararg is not None
    for n in ast.walk(node):
        if str_const(n) in KIT_MARKERS or str_const(n) == KIT_SENTINEL:
            has_marker = True
    return has_marker and has_star


argv_helpers = {fid for fid, n in func_nodes.items() if is_argv_helper(n)}


def match_path(tokens):
    """Longest manifest path at tokens[0:]."""
    for L in range(min(max_len, len(tokens)), 0, -1):
        if tuple(tokens[:L]) in paths:
            return paths[tuple(tokens[:L])]
    return None


def seq_strings(elts):
    return [str_const(e) for e in elts]


def refs_from_sequence(vals):
    """Find '<marker> path...' inside a literal string sequence (None = non-literal)."""
    found = []
    for i, v in enumerate(vals):
        if v in KIT_MARKERS or v == KIT_SENTINEL:
            toks = []
            for w in vals[i + 1 :]:
                if w is None or w.startswith("-"):
                    break
                toks.append(w)
            q = match_path(toks)
            if q:
                found.append(q)
    return found


def kit_assignments(node):
    names = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Assign) and str_const(n.value) == KIT_SENTINEL:
            for t in n.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
                elif isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
                    names.add(f"self.{t.attr}")
    return names


class_kit_attrs = defaultdict(set)
for _fid, _node in func_nodes.items():
    _mod, _qn = _fid.split(":", 1)
    if "." in _qn and ".<locals>." not in _qn:
        _cls = _qn.rsplit(".", 1)[0]
        class_kit_attrs[f"{_mod}:{_cls}"] |= {x for x in kit_assignments(_node) if x.startswith("self.")}


KIT_ATTR_NAMES = {x.split(".", 1)[1] for v in class_kit_attrs.values() for x in v}


def list_helper_param(node):
    """Index/name of a parameter p such that the body builds [<kit>, *p]."""
    params = [a.arg for a in node.args.posonlyargs + node.args.args]
    kwonly = [a.arg for a in node.args.kwonlyargs]
    KIT_NAMES.clear()
    KIT_NAMES.update(kit_assignments(node))
    for n in ast.walk(node):
        if isinstance(n, (ast.List, ast.Tuple)) and len(n.elts) >= 2:
            if str_const(n.elts[0]) == KIT_SENTINEL and isinstance(n.elts[1], ast.Starred) and isinstance(n.elts[1].value, ast.Name):
                name = n.elts[1].value.id
                if name in params:
                    return (params.index(name), name)
                if name in kwonly:
                    return (None, name)
    return None


def analyze_function(fid):
    node = func_nodes[fid]
    KIT_NAMES.clear()
    _mod, _qn = fid.split(":", 1)
    KIT_NAMES.update(class_kit_attrs.get(f"{_mod}:{_qn.rsplit('.', 1)[0]}", set()))
    for scope in enclosing_chain(fid):
        KIT_NAMES.update(x for x in kit_assignments(func_nodes[scope]) if not x.startswith("self.") or scope == fid)
    calls, refs, text_refs = set(), set(), set()
    LOCAL_INSTANCES.clear()
    for n in ast.walk(node):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name):
            ck = class_of_name(fid, n.value.func.id)
            if ck:
                for t in n.targets:
                    if isinstance(t, ast.Name):
                        LOCAL_INSTANCES[t.id] = ck
        # getattr(self, f"prefix{...}") -> all methods of own class with that prefix
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "getattr"
                and len(n.args) >= 2 and isinstance(n.args[0], ast.Name) and n.args[0].id == "self"
                and isinstance(n.args[1], ast.JoinedStr) and n.args[1].values
                and isinstance(n.args[1].values[0], ast.Constant)):
            prefix = n.args[1].values[0].value
            _m, _q = fid.split(":", 1)
            ck = f"{_m}:{_q.rsplit('.', 1)[0]}"
            calls.update(f for name, f in class_methods.get(ck, {}).items() if name.startswith(prefix))
    stack = list(node.body)
    skip_ids = set()
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if id(n) in skip_ids:
            continue
        if isinstance(n, ast.Dict):
            # lists stored under descriptive keys are guidance for humans/LLMs, not invocations
            for k, v in zip(n.keys, n.values):
                key = k.value if isinstance(k, ast.Constant) else None
                if isinstance(v, (ast.List, ast.Tuple)) and key not in ("argv", "command", "cmd"):
                    found = refs_from_sequence(seq_strings(v.elts))
                    if found:
                        text_refs.update(found)
                        skip_ids.add(id(v))
        if isinstance(n, ast.Call):
            tgt = resolve_call(fid, n.func)
            if tgt:
                calls.add(tgt)
                if tgt in argv_helpers:
                    toks = []
                    for a in n.args:
                        s = str_const(a)
                        if s is None or s.startswith("-"):
                            break
                        toks.append(s)
                    q = match_path(toks)
                    if q:
                        refs.add(q)
            if tgt in list_helpers:
                idx, pname = list_helpers[tgt]
                cand = None
                is_method = "." in tgt.split(":", 1)[1].replace(".<locals>.", "")
                pos = None if idx is None else idx - (1 if is_method else 0)
                if pos is not None and 0 <= pos < len(n.args):
                    cand = n.args[pos]
                for k in n.keywords:
                    if k.arg == pname:
                        cand = k.value
                if isinstance(cand, (ast.List, ast.Tuple)):
                    toks = []
                    for e in cand.elts:
                        v = str_const(e)
                        if v is None or v.startswith("-"):
                            break
                        toks.append(v)
                    q = match_path(toks)
                    if q:
                        refs.add(q)
            refs.update(refs_from_sequence(seq_strings(n.args)))
            # callbacks passed as arguments (e.g. step runners)
            for a in list(n.args) + [k.value for k in n.keywords]:
                if isinstance(a, (ast.Name, ast.Attribute)):
                    t = resolve_call(fid, a)
                    if t:
                        calls.add(t)
        if isinstance(n, (ast.List, ast.Tuple)):
            refs.update(refs_from_sequence(seq_strings(n.elts)))
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and "agentic-kit " in n.value:
            for chunk in n.value.split("agentic-kit ")[1:]:
                toks = []
                for w in chunk.split():
                    w = w.strip("`'\".,;:()")
                    if not w or w.startswith("-"):
                        break
                    toks.append(w)
                q = match_path(toks)
                if q:
                    text_refs.add(q)
        stack.extend(ast.iter_child_nodes(n))
    # nested defs belong to the enclosing function's behaviour (closures, step lambdas)
    for child in local_defs.get(fid, {}).values():
        calls.add(child)
    return calls, refs, text_refs


list_helpers = {}
for _fid, _node in func_nodes.items():
    lh = list_helper_param(_node)
    if lh:
        # methods: positional index shifts by one for self
        list_helpers[_fid] = lh
edges, cmd_refs, text_refs_by_fid = {}, {}, {}
for fid in func_nodes:
    edges[fid], cmd_refs[fid], text_refs_by_fid[fid] = analyze_function(fid)

# ---------------------------------------------------------------- command -> callback fid
cb_fid = {}
for q, info in callbacks.items():
    fid = f"{info['module']}:{info['qualname']}"
    if fid in func_nodes:
        cb_fid[q] = fid
    else:
        print("UNRESOLVED callback", q, fid, file=sys.stderr)
fid_to_cmd = defaultdict(set)
for q, fid in cb_fid.items():
    fid_to_cmd[fid].add(q)

# core functions owned by exactly one callback (direct non-CLI callees)
callers = defaultdict(set)
for f, ts in edges.items():
    for t in ts:
        callers[t].add(f)
callee_owners = defaultdict(set)
for q, fid in cb_fid.items():
    for t in edges[fid]:
        if t not in fid_to_cmd and t not in argv_helpers and t not in list_helpers:
            callee_owners[t].add(q)
# generic utilities verified manually as non-semantic links (logging, paths, payload builders)
GENERIC_UTILITIES = {"_emit", "_error", "default_python", "default_os_tmp_root", "is_kit_self_hosting", "_payload", "_python"}
core_owner = {}
for t, o in callee_owners.items():
    if t.split(":", 1)[1].rsplit(".", 1)[-1] in GENERIC_UTILITIES:
        continue
    non_orch = {x for x in o if by_name[x]["surface"] != "orchestrator"}
    if len(non_orch) == 1 and len(callers[t]) <= 8:
        core_owner[t] = next(iter(non_orch))


def reach(start):
    seen, stack = {start}, [start]
    while stack:
        f = stack.pop()
        for t in edges.get(f, ()):
            if t not in seen:
                seen.add(t)
                stack.append(t)
    return seen


result = {}
for c in manifest:
    q = c["qualified_name"]
    start = cb_fid[q]
    R = reach(start)
    sub, txt = set(), set()
    for f in R:
        sub |= cmd_refs[f]
        txt |= text_refs_by_fid[f]
    inproc_cb = {cmd for f in R if f != start for cmd in fid_to_cmd.get(f, ())}
    inproc_core = {core_owner[f] for f in R if f in core_owner and core_owner[f] != q}
    core_links = {core_owner[f]: f for f in sorted(R) if f in core_owner and core_owner[f] != q}
    sub.discard(q)
    inproc_cb.discard(q)
    result[q] = {
        "subprocess": sorted(sub),
        "text_mentions_only": sorted(txt - sub - {q}),
        "inprocess_callback": sorted(inproc_cb),
        "inprocess_core": sorted(inproc_core - inproc_cb),
        "core_links": core_links,
        "reachable_functions": len(R),
    }

json.dump(
    {
        "core_owner": core_owner,
        "argv_helpers": sorted(argv_helpers),
        "list_helpers": sorted(list_helpers),
        "orchestrators": result,
        "global_refs": sorted({r for v in cmd_refs.values() for r in v}),
        "ref_sites": {q: sorted(f for f, rs in cmd_refs.items() if q in rs) for q in by_name},
    },
    open(out_path, "w"),
    indent=1,
)
print("functions", len(func_nodes), "helpers", len(argv_helpers), "callbacks", len(cb_fid))
