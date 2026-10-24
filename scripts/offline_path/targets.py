"""Map current registered CLI callbacks without invoking them."""
import inspect
import json
from pathlib import Path
import sys

from typer.main import get_command
from agentic_project_kit.cli import app


def collect(command, prefix=(), output=None):
    output = {} if output is None else output
    for name, child in getattr(command, 'commands', {}).items():
        path = (*prefix, name)
        if getattr(child, 'commands', None):
            collect(child, path, output)
        elif child.callback:
            fn = inspect.unwrap(child.callback)
            file = Path(inspect.getsourcefile(fn))
            relative = 'agentic_project_kit/' + str(file).split('/agentic_project_kit/', 1)[1]
            target = output.setdefault(f'{relative}:{fn.__code__.co_firstlineno}',
                                       {'commands': [], 'function': fn.__name__})
            target['commands'].append('agentic-kit ' + ' '.join(path))
    return output


if __name__ == '__main__':
    Path(sys.argv[1]).write_text(json.dumps(collect(get_command(app)), sort_keys=True) + '\n')
