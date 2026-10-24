#!/usr/bin/env python3
"""Bounded work/release path experiment. No network, no writes outside an owned /tmp root.

Run with the Kit venv Python: scripts/offline_path/runner.py --root . --out <new-system-temp-directory>
A stopped scenario is preserved, reported INCOMPLETE, and exits 3. No automatic repair.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
import time

from evidence import edges, payload, trace_findings
from isolation import isolated, policy, probe

HERE = Path(__file__).resolve().parent
REMOTE = 'https://github.com/sim/kit-sim.git'


class Stop(RuntimeError):
    pass


class Experiment:
    def __init__(self, source: Path, out: Path):
        self.source, self.out = source.resolve(), out.resolve()
        if self.out.exists():
            raise ValueError('output must not exist; stopped evidence is never overwritten')
        policy(self.out)  # refuse before creating anything
        self.out.mkdir(mode=0o700)
        (self.out / 'policy.sb').write_text(policy(self.out))
        for name in ('home', 'tmp', 'bin', 'tools'):
            (self.out / name).mkdir()
        for file in HERE.glob('*.py'):
            shutil.copy2(file, self.out / 'tools' / file.name)
        self.work = self.out / 'work'
        self.origin = self.out / 'origin.git'
        self.steps = []
        self.start = time.monotonic()
        self.env = {'HOME': str(self.out / 'home'), 'TMPDIR': str(self.out / 'tmp'),
                    'PATH': f'{self.out}/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin',
                    'LANG': 'en_US.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1',
                    'GIT_CONFIG_GLOBAL': str(self.out / 'gitconfig'), 'GIT_CONFIG_NOSYSTEM': '1',
                    'GIT_TERMINAL_PROMPT': '0', 'GH_TOKEN': 'offline-fixture-only',
                    'FAKE_GH_DB': str(self.out / 'github.json'), 'FAKE_GH_ORIGIN': str(self.origin),
                    'FAKE_GH_LOG': str(self.out / 'github-calls.jsonl')}
        (self.out / 'gitconfig').write_text(
            '[user]\n name = Offline Fixture\n email = fixture@example.invalid\n'
            '[init]\n defaultBranch = main\n'
            f'[url "{self.origin}"]\n insteadOf = {REMOTE}\n'
            '[protocol]\n allow = never\n[protocol "file"]\n allow = always\n')
        self.base = self.read_git('rev-parse', 'HEAD')
        self.result = {'schema_version': 1, 'kind': 'offline_path_observation',
                       'source_commit': self.base, 'status': 'INCOMPLETE',
                       'assumptions': ['local bare Git origin', 'fake GitHub', 'CI test always successful',
                                       'no live publication or external consumer tested'],
                       'tool_hashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                       for p in sorted(HERE.glob('*.py'))}}

    def read_git(self, *args):
        return subprocess.run(['/usr/bin/git', '-C', str(self.source), *args], check=True,
                              text=True, capture_output=True).stdout.strip()

    def raw(self, argv, cwd=None, timeout=900):
        remaining = 2700 - (time.monotonic() - self.start)
        if remaining <= 0:
            raise Stop('overall 45-minute limit reached')
        return isolated(argv, root=self.out, cwd=cwd or self.out, env=self.env,
                        timeout=min(timeout, max(1, int(remaining))))

    def setup(self):
        self.result['isolation_probe'] = probe(self.out, sys.executable, self.env)
        self.work.mkdir()
        archive = subprocess.run(['/usr/bin/git', '-C', str(self.source), 'archive', self.base],
                                 check=True, capture_output=True).stdout
        (self.out / 'tree.tar').write_bytes(archive)
        for argv, cwd in [(['/usr/bin/tar', '-xf', str(self.out / 'tree.tar')], self.work),
                          (['/usr/bin/git', 'init', '-q', '-b', 'main'], self.work),
                          (['/usr/bin/git', 'add', '-A'], self.work),
                          (['/usr/bin/git', 'commit', '-qm', 'Seed offline fixture (#2505)'], self.work),
                          (['/usr/bin/git', 'clone', '-q', '--bare', str(self.work), str(self.origin)], self.out),
                          (['/usr/bin/git', 'remote', 'add', 'origin', REMOTE], self.work),
                          (['/usr/bin/git', 'fetch', '-q', 'origin'], self.work),
                          (['/usr/bin/git', 'branch', '--set-upstream-to=origin/main', 'main'], self.work),
                          ([sys.executable, '-m', 'venv', '--without-pip', str(self.work / '.venv')], self.out)]:
            done = self.raw(argv, cwd)
            if done.returncode:
                raise Stop(f'fixture setup failed: {argv} {done.stderr}')
        import tomllib
        version = tomllib.loads((self.work / 'pyproject.toml').read_text())['project']['version']
        done = self.raw(['/usr/bin/git', 'tag', 'v' + version], self.work)
        if done.returncode:
            raise Stop(f'fixture version tag failed: {done.stderr}')
        python = str(self.work / '.venv/bin/python')
        sites = next((self.work / '.venv/lib').glob('python*/site-packages'))
        dependencies = Path(sysconfig.get_path('purelib'))
        (sites / 'offline.pth').write_text(f'{self.work}/src\n{dependencies}\n{self.out}/tools\nimport callback_trace\n')
        kit = self.work / '.venv/bin/agentic-kit'
        kit.write_text(f'#!{python}\nfrom agentic_project_kit.cli import app\napp()\n')
        kit.chmod(0o700)
        for name, module in [('gh', 'fake_gh.py'), ('git', 'git_shim.py')]:
            script = self.out / 'bin' / name
            script.write_text(f'#!{python}\nexec(compile(open({str(self.out / "tools" / module)!r}).read(), {module!r}, "exec"))\n')
            script.chmod(0o700)
        self.env['PATH'] = f'{self.out}/bin:{kit.parent}:' + self.env['PATH'].split(':', 1)[1]
        (self.out / 'github.json').write_text(json.dumps({'next': 2506, 'prs': {}}))
        done = self.raw([python, '-I', str(self.out / 'tools/targets.py'), str(self.out / 'targets.json')], self.work)
        if done.returncode:
            raise Stop(f'callback mapping failed: {done.stderr}')
        done = self.raw([python, '-I', '-c', 'import agentic_project_kit; print(agentic_project_kit.__file__)'], self.work)
        if done.returncode or not done.stdout.strip().startswith(str(self.work / 'src') + '/'):
            raise Stop(f'fixture interpreter imports the wrong Kit: {done.stdout} {done.stderr}')
        self.env.update(OFFLINE_TRACE=str(self.out / 'callbacks.jsonl'),
                        OFFLINE_TARGETS=str(self.out / 'targets.json'), OFFLINE_SOURCE=str(self.work / 'src'))
        self.result['fixture_transformations'] = ['archive of pinned source tree, synthetic one-commit Git history', 'local version tag at synthetic seed', 'neutral comment as simulated product edit']
        targets = json.loads((self.out / 'targets.json').read_text())
        self.result['callback_targets'] = len(targets)
        self.result['registered_commands'] = sum(len(t['commands']) for t in targets.values())
        self.result['alias_callbacks'] = [t for t in targets.values() if len(t['commands']) > 1]

    def step(self, name, *args, allowed=('PASS', 'NOOP', 'READY', 'COMPLETE', 'COMPLETED'), json_required=True):
        self.env['OFFLINE_STEP'] = name
        argv = [str(self.work / '.venv/bin/agentic-kit'), *args]
        started = time.monotonic()
        try:
            done = self.raw(argv, self.work)
        except subprocess.TimeoutExpired as exc:
            done = subprocess.CompletedProcess(argv, 124, exc.stdout or '', exc.stderr or 'TIMEOUT')
        data = payload(done.stdout)
        status = data.get('result_status', data.get('status'))
        rec = {'name': name, 'argv': ['agentic-kit', *args], 'rc': done.returncode,
               'result_status': status, 'seconds': round(time.monotonic() - started, 3)}
        self.steps.append(rec)
        number = len(self.steps)
        (self.out / f'{number:02d}.stdout').write_text(done.stdout)
        (self.out / f'{number:02d}.stderr').write_text(done.stderr)
        print(json.dumps(rec), flush=True)
        if done.returncode or (json_required and status not in allowed):
            raise Stop(f'{name}: rc={done.returncode} status={status}; see step {number}')
        return data

    def run(self):
        try:
            self.setup()
            self.step('acknowledge', 'rules', 'acknowledge', json_required=False)
            self.step('bootstrap handoff', 'transfer', 'post-merge-settle', '--after-pr', '2505', '--json')
            self.step('sync main', 'transfer', 'sync-main', '--json')
            self.step('start work', 'work', 'start', '--branch', 'codex/offline-note', '--json')
            note = self.work / 'src/agentic_project_kit/__init__.py'
            note.write_text(note.read_text() + '\n# Offline simulation marker.\n')
            finish = ['work', 'finish', '--branch', 'codex/offline-note', '--title', 'Add offline fixture note',
                      '--message', 'Add offline fixture note', '--path', 'src/agentic_project_kit/__init__.py',
                      '--release-note-category', 'Changed', '--json']
            self.step('finish plan', *finish, allowed=('AWAITING_APPROVAL', 'PASS', 'PLANNED'))
            self.step('finish work', *finish, '--execute')
            self.step('sync completed work', 'transfer', 'sync-main', '--json')
            self.step('handoff', 'transfer', 'chat-switch-complete', '--json')
            # Current source is the Kit self-hosting project: use its real release policy.
            import tomllib
            version = tomllib.loads((self.work / 'pyproject.toml').read_text())['project']['version']
            major, minor, patch = map(int, version.split('.'))
            version = f'{major}.{minor}.{patch + 1}'
            self.result['synthetic_release_version'] = version
            base = ['release', 'run', '--version', version, '--json']
            release = self.step('release plan', *base, allowed=('AWAITING_APPROVAL',))
            # Observe B4 and stop before simulated publication; later gates require new model scope.
            gate = release.get('gate') or {}
            if (gate.get('gate_id') != 'B4' or gate.get('version') != version
                    or gate.get('tag') != 'v' + version or not gate.get('approval_signature')):
                raise Stop('release B4 does not match the bounded synthetic release')
            boundary = self.step('release B4', *base, '--execute', '--expected-signature', gate['approval_signature'],
                      '--approved-by', 'offline-fixture', '--consent-source', 'isolated synthetic experiment',
                      allowed=('AWAITING_APPROVAL',))
            next_gate = boundary.get('gate') or {}
            if (next_gate.get('gate_id'), next_gate.get('version'), next_gate.get('tag')) != ('C2', version, 'v' + version):
                raise Stop('unexpected gate after B4; expected the C2 publication boundary')
            self.result['publication_boundary'] = {'gate': 'C2', 'approved': False}
            self.result['status'] = 'BOUNDED_COMPLETE'
            self.result['stop_reason'] = 'intentional boundary before C2 publication approval; B4-only release observation'
        except (Stop, OSError, ValueError, subprocess.SubprocessError) as exc:
            self.result['stop_reason'] = str(exc)
        finally:
            events_file = self.out / 'callbacks.jsonl'
            events = [json.loads(line) for line in events_file.read_text().splitlines()] if events_file.exists() else []
            findings = trace_findings(events, self.steps)
            if findings:
                self.result['status'] = 'INCOMPLETE'
                self.result['stop_reason'] = 'instrumentation incomplete: ' + '; '.join(findings)
            self.result['instrumentation_findings'] = findings
            self.result.update(steps=self.steps, callback_entries=len(events), direct_edges=edges(events),
                               ambiguous_entries=sum(e['command'] == '<ambiguous>' for e in events),
                               duration_seconds=round(time.monotonic() - self.start, 3))
            (self.out / 'observation.json').write_text(json.dumps(self.result, indent=2, sort_keys=True) + '\n')
            print(f"RESULT={self.result['status']} REASON={self.result.get('stop_reason')}", flush=True)
        return 0 if self.result['status'] == 'BOUNDED_COMPLETE' else 3


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(Experiment(args.root, args.out).run())
