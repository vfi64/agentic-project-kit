import subprocess

import pytest

from agentic_project_kit.gui_state_signature import repository_preview_signature
from tests.test_gui_cockpit import _init_git_repo


def git(root, *args):
    return subprocess.run(
        ['git', '-c', 'user.name=GUI fixture', '-c', 'user.email=gui-fixture@example.invalid',
         '-c', 'commit.gpgsign=false', *args],
        cwd=root, check=True, capture_output=True, text=True,
    ).stdout


def test_signature_catches_same_path_edits_staging_and_head_changes(tmp_path):
    root = _init_git_repo(tmp_path / 'repository')
    file = root / 'draft.txt'
    file.write_text('first')
    git(root, 'add', 'draft.txt')
    git(root, 'commit', '-m', 'fixture')
    original = repository_preview_signature(root)
    file.write_text('second')
    status = git(root, 'status', '--porcelain')
    second = repository_preview_signature(root)
    file.write_text('third')
    assert git(root, 'status', '--porcelain') == status
    third = repository_preview_signature(root)
    assert len({original, second, third}) == 3
    git(root, 'add', 'draft.txt')
    staged = repository_preview_signature(root)
    assert staged != third
    git(root, 'commit', '-m', 'changed head')
    assert repository_preview_signature(root) != original


def test_signature_catches_untracked_content_and_supports_rename_and_symlink(tmp_path):
    root = _init_git_repo(tmp_path / 'repository')
    git(root, 'commit', '--allow-empty', '-m', 'initial fixture')
    file = root / 'new file.txt'
    file.write_text('one')
    first = repository_preview_signature(root)
    file.write_text('two')
    assert repository_preview_signature(root) != first
    git(root, 'add', '.')
    git(root, 'commit', '-m', 'fixture')
    git(root, 'mv', 'new file.txt', 'renamed.txt')
    renamed = repository_preview_signature(root)
    (root / 'link').symlink_to('renamed.txt')
    assert repository_preview_signature(root) != renamed


def test_signature_fails_closed_without_a_repository(tmp_path):
    with pytest.raises(RuntimeError, match='Cannot verify'):
        repository_preview_signature(tmp_path)
