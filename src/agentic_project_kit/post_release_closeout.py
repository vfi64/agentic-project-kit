from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
import re

from agentic_project_kit.post_release import build_post_release_report
from agentic_project_kit.release import CommandResult


CommandRunner = Callable[[Path, Sequence[str]], CommandResult]
HttpGetter = Callable[[str], tuple[int, str]]

EXPECTED_DOI_CLOSEOUT_PATHS: tuple[str, ...] = (
    "README.md",
    "CHANGELOG.md",
    "CITATION.cff",
    "docs/STATUS.md",
    "docs/handoff/CURRENT_HANDOFF.md",
    "docs/releases/VERIFIED_RELEASES.md",
)

_ALLOWED_WRITE_PATHS = frozenset(EXPECTED_DOI_CLOSEOUT_PATHS)


@dataclass(frozen=True)
class PostReleaseDoiCloseoutResult:
    version: str
    result_status: str
    returncode: int
    write: bool
    blockers: tuple[str, ...]
    changed_paths: tuple[str, ...]
    expected_paths: tuple[str, ...]
    version_doi: str
    concept_doi: str
    next_action: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.blockers

    def as_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "result_status": self.result_status,
            "returncode": self.returncode,
            "write": self.write,
            "blockers": list(self.blockers),
            "changed_paths": list(self.changed_paths),
            "expected_paths": list(self.expected_paths),
            "version_doi": self.version_doi,
            "concept_doi": self.concept_doi,
            "next_action": self.next_action,
            "ok": self.ok,
        }


def post_release_doi_closeout(
    project_root: Path,
    *,
    version: str,
    write: bool = False,
    command_runner: CommandRunner | None = None,
    http_getter: HttpGetter | None = None,
) -> PostReleaseDoiCloseoutResult:
    report = build_post_release_report(
        project_root,
        version=version,
        command_runner=command_runner,
        http_getter=http_getter,
    )
    github_status, _ = _check_detail(report, "GitHub release")
    concept_status, concept_detail = _check_detail(report, "Zenodo concept DOI")
    version_status, version_detail = _check_detail(report, "Zenodo version DOI")
    concept_doi = _extract_zenodo_doi(concept_detail)
    version_doi = _extract_zenodo_doi(version_detail)
    blockers: list[str] = []
    if github_status != "PASS":
        blockers.append("github_release_not_verified")
    if concept_status != "PASS" or not concept_doi:
        blockers.append("zenodo_concept_doi_not_verified")
    if version_status != "PASS" or not version_doi:
        blockers.append("zenodo_version_doi_not_verified")
    if blockers:
        return PostReleaseDoiCloseoutResult(
            version,
            "BLOCKED",
            2,
            write,
            tuple(blockers),
            (),
            EXPECTED_DOI_CLOSEOUT_PATHS,
            version_doi,
            concept_doi,
            "Wait for post-release-check PASS before writing DOI metadata.",
        )

    updaters = _metadata_updaters(version, version_doi, concept_doi)
    changed_texts: dict[str, str] = {}
    changed_paths: list[str] = []
    blocked_write_paths = tuple(sorted(set(updaters) - _ALLOWED_WRITE_PATHS))
    if write and blocked_write_paths:
        blockers.extend(f"unexpected_write_path:{path}" for path in blocked_write_paths)

    candidate_texts: dict[str, str] = {}
    for relative_path, updater in updaters.items():
        path = project_root / relative_path
        if not path.exists():
            blockers.append(f"missing_metadata_file:{relative_path}")
            continue
        old = path.read_text(encoding="utf-8")
        new = updater(old)
        candidate_texts[relative_path] = new
        if new != old:
            changed_paths.append(relative_path)
            changed_texts[relative_path] = new

    blockers.extend(
        _current_release_metadata_consistency_blockers(
            candidate_texts,
            version=version,
            version_doi=version_doi,
            concept_doi=concept_doi,
        )
    )

    if blockers:
        next_action = "Create the missing release metadata files before DOI closeout."
        if any(blocker.startswith("unexpected_write_path:") for blocker in blockers):
            next_action = "Refuse --write until DOI closeout only targets the approved release metadata files."
        elif any(blocker.startswith("current_release_metadata_inconsistent:") for blocker in blockers):
            next_action = "Fix current-release DOI metadata consistency before DOI closeout can write."
        return PostReleaseDoiCloseoutResult(
            version,
            "BLOCKED",
            2,
            write,
            tuple(blockers),
            tuple(changed_paths),
            EXPECTED_DOI_CLOSEOUT_PATHS,
            version_doi,
            concept_doi,
            next_action,
        )

    if write:
        for relative_path, text in changed_texts.items():
            (project_root / relative_path).write_text(text, encoding="utf-8")

    next_action = (
        "Post-release DOI metadata closeout is complete."
        if write
        else "Dry run passed; rerun with --write to update DOI metadata."
    )
    return PostReleaseDoiCloseoutResult(
        version,
        "PASS",
        0,
        write,
        (),
        tuple(changed_paths),
        EXPECTED_DOI_CLOSEOUT_PATHS,
        version_doi,
        concept_doi,
        next_action,
    )


def render_post_release_doi_closeout_result(result: PostReleaseDoiCloseoutResult) -> str:
    lines = [
        "POST_RELEASE_DOI_CLOSEOUT",
        f"STATE={result.result_status}",
        f"VERSION={result.version}",
        f"VERSION_DOI={result.version_doi}",
        f"CONCEPT_DOI={result.concept_doi}",
        f"WRITE={str(result.write).lower()}",
        f"RETURNCODE={result.returncode}",
    ]
    lines.extend(f"EXPECTED_PATH={path}" for path in result.expected_paths)
    lines.extend(f"CHANGED_PATH={path}" for path in result.changed_paths)
    missing_changed = sorted(set(result.expected_paths) - set(result.changed_paths))
    if not result.changed_paths:
        lines.append("CHANGED_PATH=<none>")
    lines.extend(f"UNCHANGED_EXPECTED_PATH={path}" for path in missing_changed)
    lines.extend(f"BLOCKER={blocker}" for blocker in result.blockers)
    lines.append(f"NEXT={result.next_action}")
    lines.append("FINAL_SIGNAL=d" if result.ok else "FINAL_SIGNAL=f")
    return "\n".join(lines) + "\n"


def _check_detail(report, name: str) -> tuple[str, str]:
    for check in report.checks:
        if check.name == name:
            return str(check.status.value), check.detail
    return "MISSING", ""


def _extract_zenodo_doi(text: str) -> str:
    match = re.search(r"10\.5281/zenodo\.\d+", text)
    return match.group(0) if match else ""


def _current_release_metadata_consistency_blockers(
    texts: Mapping[str, str],
    *,
    version: str,
    version_doi: str,
    concept_doi: str,
) -> tuple[str, ...]:
    tag = f"v{version}"
    expected_by_path = {
        "README.md": (
            f"Current verified release: `{tag}` with Zenodo version DOI `{version_doi}`.",
        ),
        "docs/STATUS.md": (
            f"Current version: {version}",
            f"Current verified release: {version}.",
            f"Current release tag: {tag}.",
            f"Verified Zenodo version DOI: `{version_doi}`.",
        ),
        "docs/handoff/CURRENT_HANDOFF.md": (
            f"Current version: {version}",
            f"- Current verified release: {version}.",
            f"- Current release tag: {tag}.",
            f"- Verified Zenodo version DOI: `{version_doi}`.",
        ),
        "CITATION.cff": (f"# Verified {tag} version DOI: {version_doi}",),
        "CHANGELOG.md": (
            f"Zenodo {tag} DOI: {version_doi}",
            f"Zenodo concept DOI `{concept_doi}`",
        ),
        "docs/releases/VERIFIED_RELEASES.md": (
            f"- `{tag}` / `{version}`: Zenodo version DOI `{version_doi}`; concept DOI `{concept_doi}`.",
        ),
    }
    blockers: list[str] = []
    for relative_path, expected_lines in expected_by_path.items():
        text = texts.get(relative_path)
        if text is None:
            blockers.append(f"current_release_metadata_inconsistent:{relative_path}:missing_candidate_text")
            continue
        for expected in expected_lines:
            if expected not in text:
                blockers.append(f"current_release_metadata_inconsistent:{relative_path}")
                break
    return tuple(blockers)


def _metadata_updaters(version: str, doi: str, concept_doi: str) -> dict[str, Callable[[str], str]]:
    tag = f"v{version}"

    def update_readme(text: str) -> str:
        text = re.sub(
            r"^Prepared release: `v[^`]+`; GitHub Release, tag publication, and Zenodo version DOI verification are [^.]+\.",
            f"Prepared release: `{tag}`; GitHub Release, tag publication, and Zenodo version DOI verification are complete.",
            text,
            count=1,
            flags=re.MULTILINE,
        )
        line = f"Current verified release: `{tag}` with Zenodo version DOI `{doi}`."
        if re.search(r"^Current verified release:\s+.*$", text, re.MULTILINE):
            return re.sub(r"^Current verified release:\s+.*$", line, text, count=1, flags=re.MULTILINE)
        return text.rstrip() + "\n" + line + "\n"

    def update_status(text: str) -> str:
        return _update_current_release_block(
            text,
            version=version,
            tag=tag,
            doi=doi,
            bullet_prefix="",
        )

    def update_handoff(text: str) -> str:
        return _update_current_release_block(
            text,
            version=version,
            tag=tag,
            doi=doi,
            bullet_prefix="- ",
        )

    def update_citation(text: str) -> str:
        line = f"# Verified {tag} version DOI: {doi}"
        if line in text:
            return text
        marker = re.search(
            r"^# Verified v[0-9]+\.[0-9]+\.[0-9]+ version DOI: 10\.5281/zenodo\.\d+$",
            text,
            re.MULTILINE,
        )
        if marker:
            return text[: marker.end()] + "\n" + line + text[marker.end() :]
        return text.rstrip() + "\n" + line + "\n"

    def update_changelog(text: str) -> str:
        if f"Zenodo {tag} DOI: {doi}" in text:
            return text
        first_next = text.find("\n## v", 1)
        addition = (
            "\n\nPost-release verification complete: GitHub Release exists, "
            f"Zenodo concept DOI `{concept_doi}`, verified {tag} DOI `{doi}`."
            f"\n\nZenodo {tag} DOI: {doi}"
        )
        if first_next == -1:
            return text.rstrip() + addition + "\n"
        return text[:first_next].rstrip() + addition + text[first_next:]

    def update_verified_releases(text: str) -> str:
        line = f"- `{tag}` / `{version}`: Zenodo version DOI `{doi}`; concept DOI `{concept_doi}`."
        lines = [
            existing
            for existing in text.splitlines()
            if not (
                re.search(rf"`?{re.escape(tag)}`?\b|`?{re.escape(version)}`?\b", existing)
                and doi in existing
            )
        ]
        insert_at = next(
            (i + 1 for i, existing in enumerate(lines) if re.search(r"`v0\.4\.5`|v0\.4\.5", existing)),
            len(lines),
        )
        lines.insert(insert_at, line)
        return "\n".join(lines) + "\n"

    return {
        "README.md": update_readme,
        "docs/STATUS.md": update_status,
        "docs/handoff/CURRENT_HANDOFF.md": update_handoff,
        "CITATION.cff": update_citation,
        "CHANGELOG.md": update_changelog,
        "docs/releases/VERIFIED_RELEASES.md": update_verified_releases,
    }


def _update_current_release_block(text: str, *, version: str, tag: str, doi: str, bullet_prefix: str) -> str:
    start_match = re.search(rf"^Current version:\s*{re.escape(version)}\s*$", text, re.MULTILINE)
    if not start_match:
        return text

    next_current = re.search(r"^Current version:\s*", text[start_match.end() :], re.MULTILINE)
    end = start_match.end() + next_current.start() if next_current else len(text)

    before = text[: start_match.start()]
    block = text[start_match.start() : end]
    after = text[end:]

    verified = f"{bullet_prefix}Current verified release: {version}."
    release_tag = f"{bullet_prefix}Current release tag: {tag}."
    doi_line = f"{bullet_prefix}Verified Zenodo version DOI: `{doi}`."

    if bullet_prefix:
        block = re.sub(r"^- Current verified release.*$", verified, block, count=1, flags=re.MULTILINE)
        block = re.sub(r"^- Prepared release tag: .*$", release_tag, block, count=1, flags=re.MULTILINE)
        block = re.sub(r"^- Current release tag: .*$", release_tag, block, count=1, flags=re.MULTILINE)
        block = re.sub(
            r"^- Verified Zenodo version DOI: `10\.5281/zenodo\.\d+`\.",
            doi_line,
            block,
            count=1,
            flags=re.MULTILINE,
        )
    else:
        block = re.sub(r"^Current verified release.*$", verified, block, count=1, flags=re.MULTILINE)
        block = re.sub(r"^Prepared release tag: .*$", release_tag, block, count=1, flags=re.MULTILINE)
        block = re.sub(r"^Current release tag: .*$", release_tag, block, count=1, flags=re.MULTILINE)
        block = re.sub(
            r"^Verified Zenodo version DOI: `10\.5281/zenodo\.\d+`\.",
            doi_line,
            block,
            count=1,
            flags=re.MULTILINE,
        )
        block = re.sub(
            rf"^{re.escape(tag)} .*?(pending|prepared).*?$",
            f"{tag} GitHub Release publication and post-release Zenodo verification are complete. "
            f"Verified Zenodo version DOI: `{doi}`.",
            block,
            count=1,
            flags=re.MULTILINE,
        )

    return before + block + after
