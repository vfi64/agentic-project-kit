"""Observe CLI callback entries, including isolated Python subprocesses; no core inference."""
import json
import os
import sys
import threading

if os.environ.get('OFFLINE_TRACE'):
    with open(os.environ['OFFLINE_TARGETS']) as handle:
        targets = json.load(handle)
    source = os.environ['OFFLINE_SOURCE'] + '/'
    inherited = json.loads(os.environ.get('OFFLINE_PARENT', '[]'))
    active = []
    lock = threading.RLock()
    sequence = 0
    cache = {}
    files = {source + key.rsplit(':', 1)[0] for key in targets}

    def profile(frame, event, arg):
        global sequence
        if event not in ('call', 'return'):
            return
        code = frame.f_code
        if code.co_filename not in files:
            return
        cached = cache.get(id(code))
        key = cached[1] if cached is not None else None
        if key is None:
            filename = code.co_filename
            relative = filename[len(source):] if filename.startswith(source) else ''
            target = targets.get(f'{relative}:{code.co_firstlineno}', {})
            choices = target.get('commands', [target.get('command')])
            matches = [name for name in choices if name and sys.argv[1:len(name.split())] == name.split()[1:]]
            command = matches[0] if len(matches) == 1 else choices[0] if len(choices) == 1 else '<ambiguous>'
            key = command if target.get('function') == code.co_name else ''
            cache[id(code)] = (code, key)
        if not key:
            return
        with lock:
            if event == 'call':
                sequence += 1
                call = {'id': f'{os.getpid()}:{sequence}', 'command': key}
                ancestors = inherited + active
                record = {**call, 'parent': ancestors[-1] if ancestors else None,
                          'ancestors': ancestors, 'pid': os.getpid(),
                          'step': os.environ.get('OFFLINE_STEP', '')}
                fd = os.open(os.environ['OFFLINE_TRACE'], os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
                try:
                    os.write(fd, (json.dumps(record, sort_keys=True) + '\n').encode())
                finally:
                    os.close(fd)
                active.append(call)
            elif active and active[-1]['command'] == key:
                active.pop()
            os.environ['OFFLINE_PARENT'] = json.dumps(inherited + active)

    sys.setprofile(profile)
    threading.setprofile(profile)
