"""Map every manifest command to its Python callback (module, qualname, file, line)."""
import inspect
import json
import sys

from typer.main import get_command
from agentic_project_kit.cli import app

root = get_command(app)
out = {}


def walk(cmd, path):
    sub = getattr(cmd, "commands", None)
    if sub:
        for name, child in sub.items():
            walk(child, path + [name])
    else:
        cb = cmd.callback
        # typer wraps callbacks; unwrap
        fn = inspect.unwrap(cb) if cb else None
        key = "agentic-kit " + " ".join(path)
        if fn is None:
            out[key] = None
            return
        try:
            src = inspect.getsourcefile(fn)
            line = inspect.getsourcelines(fn)[1]
        except Exception:
            src, line = None, None
        out[key] = {
            "module": fn.__module__,
            "qualname": fn.__qualname__,
            "file": src,
            "line": line,
        }


walk(root, [])
json.dump(out, open(sys.argv[1], "w"), indent=1)
print(len(out))
