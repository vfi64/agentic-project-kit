"""Conservative source flow for Kit command references; never executes analyzed code.

This developer analysis recognizes literal carriers, local aliases and statically
resolved helper returns/parameters. Witnesses mean possible source flow, not a
runtime trace. Unsupported mutation, dynamic dispatch and subprocess contents
are deliberately not expanded.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class Value:
    text: str | None = None
    refs: frozenset[str] = frozenset()
    argv: bool = False


def combined(values):
    return Value(refs=frozenset().union(*(v.refs for v in values)))


def merge_value(a, b):
    return Value(a.text if a.text == b.text else None, a.refs | b.refs, a.argv and b.argv)


@dataclass(frozen=True)
class Summary:
    returned: Value = Value()
    execution: frozenset[str] = frozenset()
    recommendation: frozenset[str] = frozenset()


EXECUTION = {f"subprocess.{n}" for n in ("run", "Popen", "call", "check_call", "check_output")}
DISPLAY = {"builtins.print", "typer.echo", "typer.secho", "click.echo", "click.secho"}
EXECUTABLE_RESOLVERS = {
    "agentic_project_kit.cli_executable.default_agentic_kit",
    "agentic_project_kit.cli_executable.owned_agentic_kit",
}
GUIDANCE_FIELDS = {"next_action", "next_safe_action", "rule_registry_next_action", "recommendation"}


class SourceFlow:
    def __init__(self, sources: dict[str, str], commands: list[str]):
        self.commands = sorted(commands, key=lambda s: (-len(s), s))
        self.trees = {m: ast.parse(text) for m, text in sorted(sources.items())}
        self.functions = {}
        self.imports = {}
        self.stars = {}
        self.exports = {}
        self.shadowed = {}
        self.sites = {}
        self.summaries = {}
        self.witnesses = {}
        self.transitions = set()
        self.matches = {}
        self.command_set = set(commands)
        for module, tree in self.trees.items():
            self.imports[module], self.stars[module] = {}, []
            for n in tree.body:
                if isinstance(n, ast.Import):
                    for a in n.names:
                        self.imports[module][a.asname or a.name.split('.')[0]] = a.name if a.asname else a.name.split('.')[0]
                if isinstance(n, ast.ImportFrom) and n.level == 0:
                    for a in n.names:
                        if a.name == '*':
                            self.stars[module].append(n.module)
                        else:
                            self.imports[module][a.asname or a.name] = f"{n.module}.{a.name}"
            self.shadowed[module] = {t.id for n in tree.body if isinstance(n, (ast.Assign, ast.AnnAssign))
                                     for t in (n.targets if isinstance(n, ast.Assign) else [n.target]) if isinstance(t, ast.Name)}
            export = next((n.value for n in tree.body if isinstance(n, ast.Assign)
                           and any(isinstance(t, ast.Name) and t.id == '__all__' for t in n.targets)), None)
            if export is None:
                self.exports[module] = None  # Python's default public-name export rule.
            elif ast.unparse(export) == "[name for name in globals() if not name.startswith('__')]":
                self.exports[module] = 'non_dunder'
            else:
                try:
                    value = ast.literal_eval(export)
                    self.exports[module] = set(value) if isinstance(value, (list, tuple)) and all(isinstance(x, str) for x in value) else set()
                except (ValueError, TypeError):
                    self.exports[module] = set()  # Unknown export computation is not guessed.
            self._index(module, '', tree.body)
        self.dotted_functions = {fid.replace(':', '.'): fid for fid in self.functions}

    def _index(self, module, scope, body):
        for n in body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = '.'.join(filter(None, (scope, n.name)))
                if not isinstance(n, ast.ClassDef):
                    self.functions[f"{module}:{name}"] = n
                self._index(module, name, n.body)

    def resolve(self, module, scope, node, env):
        if isinstance(node, ast.Attribute):
            base = self.resolve(module, scope, node.value, env)
            return base + '.' + node.attr if base else ''
        if not isinstance(node, ast.Name) or node.id in env:
            return ''
        parts = scope.split('.')
        for size in range(len(parts), -1, -1):
            name = '.'.join([*parts[:size], node.id])
            if f"{module}:{name}" in self.functions and (size > 0 or node.id not in self.shadowed[module]):
                return f"{module}:{name}"
        if node.id in self.shadowed[module]:
            return ''
        imported = self.imports[module].get(node.id)
        if imported:
            return self.function_id(imported) or imported
        # Star imports are ambiguous unless exactly one supplying module resolves.
        candidates = set()
        for other in self.stars[module]:
            if other not in self.exports:
                continue
            exports = self.exports[other]
            allowed = (not node.id.startswith('_') if exports is None else
                       not node.id.startswith('__') if exports == 'non_dunder' else node.id in exports)
            if not allowed or node.id in self.shadowed[other]:
                continue
            q = f"{other}:{node.id}"
            if q in self.functions and not node.id.startswith('__'):
                candidates.add(q)
            alias = self.imports.get(other, {}).get(node.id)
            if alias:
                candidates.add(self.function_id(alias) or alias)
        if len(candidates) == 1:
            return candidates.pop()
        return 'builtins.print' if node.id == 'print' and not candidates else ''

    def function_id(self, dotted):
        return self.dotted_functions.get(dotted)

    def candidate(self, fid, node, text):
        if not text:
            return frozenset()
        if text not in self.matches:
            found = set()
            for match in re.finditer(r'(?<![\w-])agentic-kit(?:\s+[a-z0-9][a-z0-9-]*)+', text):
                words = match.group().split()
                for size in range(len(words), 1, -1):
                    command = ' '.join(words[:size])
                    if command in self.command_set:
                        found.add(command)
                        break
            self.matches[text] = sorted(found)
        found = self.matches[text]
        refs = set()
        for command in found:
            key = f"{fid}:{node.lineno}:{node.col_offset}:{command}"
            self.sites[key] = {'function': fid, 'line': node.lineno, 'column': node.col_offset, 'command': command}
            refs.add(key)
        return frozenset(refs)

    def analyze(self, fid):
        node = self.functions[fid]
        module, scope = fid.split(':', 1)
        params = [a.arg for a in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)]
        local_names = set()
        pending = list(node.body)
        while pending:
            item = pending.pop()
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(item, ast.Name) and isinstance(item.ctx, (ast.Store, ast.Del)):
                local_names.add(item.id)
            if isinstance(item, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) and item.name:
                local_names.add(item.name)
            if isinstance(item, (ast.Import, ast.ImportFrom)):
                local_names.update(a.asname or a.name.split('.')[0] for a in item.names)
            pending.extend(ast.iter_child_nodes(item))
        env = {name: Value() for name in local_names}
        env.update({p: Value(refs=frozenset({f'@{i}'})) for i, p in enumerate(params)})
        execution, recommendation, returned = set(), set(), []

        def mark(refs, kind, location, via="guidance-field"):
            if refs:
                self.transitions.add((fid, location.lineno, kind, via))
            target = execution if kind == 'execution' else recommendation
            target.update(refs)
            for ref in refs:
                if not ref.startswith('@'):
                    self.witnesses.setdefault((ref, kind), set()).add(f'{fid}:{location.lineno}')

        def execution_refs(value):
            params = frozenset(r for r in value.refs if r.startswith('@'))
            if not value.argv or not value.text:
                return params
            targets = [c for c in self.commands if value.text == c or value.text.startswith(c + ' ')]
            if not targets:
                return params
            target = targets[0]
            return params | frozenset(r for r in value.refs if r in self.sites and self.sites[r]['command'] == target)

        def substitute(refs, args, executing=False):
            result = set()
            for ref in refs:
                if ref.startswith('@'):
                    i = int(ref[1:])
                    if i < len(args):
                        result.update(execution_refs(args[i]) if executing else args[i].refs)
                else:
                    result.add(ref)
            return frozenset(result)

        def invalidate(value, local):
            for key, alias in list(local.items()):
                if alias is value or (value.refs and value.refs & alias.refs):
                    local[key] = Value(refs=alias.refs)

        def expr(n, local):
            if n is None:
                return Value()
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                return Value(n.value, self.candidate(fid, n, n.value))
            if isinstance(n, ast.Name):
                return local.get(n.id, Value())
            if isinstance(n, (ast.List, ast.Tuple)):
                vals = [expr(e, local) for e in n.elts]
                # Keep literal prefixes before computed arguments; never invent the prefix.
                prefix = []
                for v in vals:
                    if v.text is None or v.argv:
                        break
                    prefix.append(v.text)
                text = ' '.join(prefix) if prefix else None
                refs = combined(vals).refs | self.candidate(fid, n, text)
                is_argv = bool(vals and vals[0].text == 'agentic-kit' and not vals[0].argv)
                return Value(text, refs, is_argv)
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
                a, b = expr(n.left, local), expr(n.right, local)
                text = a.text + b.text if a.text is not None and b.text is not None else None
                return Value(text, a.refs | b.refs | self.candidate(fid, n, text))
            if isinstance(n, ast.Dict):
                vals = []
                for key, val in zip(n.keys, n.values):
                    value = expr(val, local)
                    vals.append(value)
                    if isinstance(key, ast.Constant) and key.value in GUIDANCE_FIELDS:
                        mark(value.refs, 'recommendation', val, 'guidance-field:' + key.value)
                return combined(vals)
            if isinstance(n, ast.Call):
                name = self.resolve(module, scope, n.func, local)
                args = [expr(a, local) for a in n.args]
                kwargs = {k.arg: expr(k.value, local) for k in n.keywords if k.arg}
                if name.replace(':', '.') in EXECUTABLE_RESOLVERS:
                    return Value('agentic-kit')
                if name in EXECUTION:
                    # Shell/override kwargs may execute another program or argument shape.
                    opaque = len(n.args) > 1 or any(k.arg in {None, 'executable'} for k in n.keywords)
                    shell = next((k.value for k in n.keywords if k.arg == 'shell'), None)
                    if opaque or (shell is not None and not (isinstance(shell, ast.Constant) and shell.value is False)):
                        return Value()
                    value = args[0] if args else kwargs.get('args', Value())
                    mark(execution_refs(value), 'execution', n, name)
                    return Value()
                if name in DISPLAY:
                    mark(combined(args + list(kwargs.values())).refs, 'recommendation', n, name)
                    return Value()
                if name in self.summaries:
                    callee = self.functions[name]
                    names = [a.arg for a in (*callee.args.posonlyargs, *callee.args.args, *callee.args.kwonlyargs)]
                    actual = [args[i] if i < len(args) else kwargs.get(p, Value()) for i, p in enumerate(names)]
                    summary = self.summaries[name]
                    mark(substitute(summary.execution, actual, executing=True), 'execution', n, name)
                    mark(substitute(summary.recommendation, actual), 'recommendation', n, name)
                    for arg in [*n.args, *(kw.value for kw in n.keywords)]:
                        if isinstance(arg, ast.Name) and arg.id in local and local[arg.id].argv:
                            invalidate(local[arg.id], local)
                    return Value(summary.returned.text, substitute(summary.returned.refs, actual), summary.returned.argv)
                if name == 'shlex.join' and args:
                    return Value(args[0].text, args[0].refs)
                if (isinstance(n.func, ast.Attribute) and n.func.attr == 'join'
                        and isinstance(n.func.value, ast.Constant) and isinstance(n.func.value.value, str) and args):
                    return Value(refs=args[0].refs)
                # Unknown code may mutate argv aliases; do not carry a stale prefix forward.
                for arg in [*n.args, *(kw.value for kw in n.keywords)]:
                    if isinstance(arg, ast.Name) and arg.id in local:
                        invalidate(local[arg.id], local)
                if isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name):
                    receiver = local.get(n.func.value.id)
                    if receiver:
                        invalidate(receiver, local)
                return Value()
            if isinstance(n, ast.JoinedStr):
                return combined([expr(v.value if isinstance(v, ast.FormattedValue) else v, local) for v in n.values])
            # Local container reads and string join preserve provenance, without resolving values.
            if isinstance(n, ast.Subscript):
                return Value()  # arbitrary container indexing is deliberately unsupported
            if isinstance(n, ast.Attribute):
                return Value()
            return combined([expr(c, local) for c in ast.iter_child_nodes(n)])

        def body(statements, local):
            for s in statements:
                if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    continue
                if isinstance(s, ast.Expr):
                    if not (isinstance(s.value, ast.Constant) and isinstance(s.value.value, str)):
                        expr(s.value, local)
                elif isinstance(s, (ast.Assign, ast.AnnAssign)):
                    value = expr(s.value, local)
                    targets = s.targets if isinstance(s, ast.Assign) else [s.target]
                    for target in targets:
                        if isinstance(target, ast.Name):
                            local[target.id] = value
                        elif isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
                            invalidate(local.get(target.value.id, Value()), local)
                elif isinstance(s, (ast.AugAssign, ast.Delete)):
                    for value in list(local.values()):
                        if value.argv:
                            invalidate(value, local)
                elif isinstance(s, ast.Return):
                    returned.append(expr(s.value, local))
                    return True
                elif isinstance(s, ast.If):
                    expr(s.test, local)
                    if isinstance(s.test, ast.Constant):
                        if body(s.body if s.test.value else s.orelse, local):
                            return True
                        continue
                    left, right = dict(local), dict(local)
                    left_returned = body(s.body, left)
                    right_returned = body(s.orelse, right)
                    for key in left.keys() | right.keys():
                        local[key] = merge_value(left.get(key, Value()), right.get(key, Value()))
                    if left_returned and right_returned:
                        return True
                elif isinstance(s, (ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith)):
                    if isinstance(s, ast.While):
                        expr(s.test, local)
                        if isinstance(s.test, ast.Constant) and not s.test.value:
                            body(s.orelse, local)
                            continue
                    if isinstance(s, (ast.For, ast.AsyncFor)):
                        expr(s.iter, local)
                    if isinstance(s, (ast.With, ast.AsyncWith)):
                        for item in s.items:
                            expr(item.context_expr, local)
                    # Visit potential bodies once, merge with zero iterations. No path guarantee.
                    before, after = dict(local), dict(local)
                    bindings = [s.target] if isinstance(s, (ast.For, ast.AsyncFor)) else [item.optional_vars for item in s.items] if isinstance(s, (ast.With, ast.AsyncWith)) else []
                    for binding in bindings:
                        if binding:
                            for target in ast.walk(binding):
                                if isinstance(target, ast.Name):
                                    after[target.id] = Value()
                    body(s.body, after)
                    for key in before.keys() | after.keys():
                        local[key] = merge_value(before.get(key, Value()), after.get(key, Value()))
                    body(getattr(s, 'orelse', []), local)
                elif isinstance(s, ast.Try):
                    branches = [s.body, s.orelse, s.finalbody, *(h.body for h in s.handlers)]
                    for branch in branches:
                        after = dict(local)
                        body(branch, after)
                        for key in local.keys() | after.keys():
                            local[key] = merge_value(local.get(key, Value()), after.get(key, Value()))
                elif not isinstance(s, (ast.Pass, ast.Import, ast.ImportFrom, ast.Raise, ast.Assert)):
                    # Unsupported statements must not preserve potentially mutated argv.
                    for value in list(local.values()):
                        if value.argv:
                            invalidate(value, local)
        body(node.body, env)
        ret = returned[0] if returned else Value()
        for value in returned[1:]:
            ret = merge_value(ret, value)
        return Summary(ret, frozenset(execution), frozenset(recommendation))

    def run(self, max_rounds=16):
        if max_rounds < 1:
            raise ValueError("max_rounds must be positive")
        converged = False
        for round_no in range(1, max_rounds + 1):
            self.witnesses = {}
            self.transitions = set()
            current = {fid: self.analyze(fid) for fid in sorted(self.functions)}
            if current == self.summaries:
                converged = True
                break
            self.summaries = current
        rows = []
        for ref, site in sorted(self.sites.items()):
            kinds = [k for k in ('execution', 'recommendation') if (ref, k) in self.witnesses]
            rows.append({**site, 'classification': 'mixed' if len(kinds) == 2 else kinds[0] if kinds else 'unknown',
                         'witnesses': {k: sorted(self.witnesses[ref, k]) for k in kinds}})
        return {'converged': converged, 'rounds': round_no, 'sites': rows,
                'transitions': [{'function': f, 'line': line, 'kind': kind, 'callee': callee}
                                for f, line, kind, callee in sorted(self.transitions)]}


def load_sources(root: Path):
    result = {}
    for path in sorted((root / 'src/agentic_project_kit').rglob('*.py')):
        parts = path.relative_to(root / 'src').with_suffix('').parts
        module = '.'.join(parts[:-1] if parts[-1] == '__init__' else parts)
        result[module] = path.read_text()
    return result
