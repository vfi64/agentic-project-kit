from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
import re

from agentic_project_kit.post_release import build_post_release_report
from agentic_project_kit.release import CommandResult


CommandRunner = Callable[[Path, Sequence[str]], CommandResult]
HttpGetter = Callable[[str], tuple[int, str]]


@dataclass(frozen=True)
class PostReleaseDoiCloseoutResult:
    version: str
    result_status: str
    returncode: int
    write: bool
    blockers: tuple[str, ...]
    changed_paths: tuple[str, ...]
    version_doi: str
    concept_doi: str
    next_action: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.blockers


def post_release_doi_closeout(project_root: Path, *, version: str, write: bool = False,
    command_runner: CommandRunner | None = None, http_getter: HttpGetter | None = None) -> PostReleaseDoiCloseoutResult:
    report = build_post_release_report(project_root, version=version, command_runner=command_runner, http_getter=http_getter)
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
        return PostReleaseDoiCloseoutResult(version, "BLOCKED", 2, write, tuple(blockers), (), version_doi, concept_doi, "Wait for post-release-check PASS before writing DOI metadata.")

    changed_paths: list[str] = []
    for relative_path, updater in _metadata_updaters(version, version_doi, concept_doi).items():
        path = project_root / relative_path
        if not path.exists():
            blockers.append(f"missing_metadata_file:{relative_path}")
            continue
        old = path.read_text(encoding="utf-8")
        new = updater(old)
        if new != old:
            changed_paths.append(relative_path)
            if write:
                path.write_text(new, encoding="utf-8")
    if blockers:
        return PostReleaseDoiCloseoutResult(version, "BLOCKED", 2, write, tuple(blockers), tuple(changed_paths), version_doi, concept_doi, "Create the missing release metadata files before DOI closeout.")
    next_action = "Post-release DOI metadata closeout is complete." if write else "Dry run passed; rerun with --write to update DOI metadata."
    return PostReleaseDoiCloseoutResult(version, "PASS", 0, write, (), tuple(changed_paths), version_doi, concept_doi, next_action)


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
    lines.extend(f"CHANGED_PATH={path}" for path in result.changed_paths)
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


def _metadata_updaters(version: str, doi: str, concept_doi: str) -> dict[str, Callable[[str], str]]:
    tag = f"v{version}"

    def update_readme(text: str) -> str:
        text = re.sub(r"^Prepared release: `v[^`]+`; GitHub Release, tag publication, and Zenodo version DOI verification are [^.]+\.",
                      f"Prepared release: `{tag}`; GitHub Release, tag publication, and Zenodo version DOI verification are complete.",
                      text, count=1, flags=re.MULTILINE)
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
        marker = re.search(r"^# Verified v[0-9]+\.[0-9]+\.[0-9]+ version DOI: 10\.5281/zenodo\.\d+$", text, re.MULTILINE)
        if marker:
            return text[: marker.end()] + "\n" + line + text[marker.end():]
        return text.rstrip() + "\n" + line + "\n"

    def update_changelog(text: str) -> str:
        if f"Zenodo {tag} DOI: {doi}" in text:
            return text
        first_next = text.find("\n## v", 1)
        addition = f"\n\nPost-release verification complete: GitHub Release exists, Zenodo concept DOI `{concept_doi}`, verified {tag} DOI `{doi}`.\n\nZenodo {tag} DOI: {doi}"
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

    next_current = re.search(r"^Current version:\s*", text[start_match.end():], re.MULTILINE)
    end = start_match.end() + next_current.start() if next_current else len(text)

    before = text[:start_match.start()]
    block = text[start_match.start():end]
    after = text[end:]

    verified = f"{bullet_prefix}Current verified release: {version}."
    release_tag = f"{bullet_prefix}Current release tag: {tag}."
    doi_line = f"{bullet_prefix}Verified Zenodo version DOI: `{doi}`."

    if bullet_prefix:
        block = re.sub(r"^- Current verified release.*$", verified, block, count=1, flags=re.MULTILINE)
        block = re.sub(r"^- Prepared release tag: .*$", release_tag, block, count=1, flags=re.MULTILINE)
        block = re.sub(r"^- Current release tag: .*$", release_tag, block, count=1, flags=re.MULTILINE)
        block = re.sub(r"^- Verified Zenodo version DOI: `10\\.5281/zenodo\\.\\d+`\\.", doi_line, block, count=1, flags=re.MULTILINE)
    else:
        block = re.sub(r"^Current verified release.*$", verified, block, count=1, flags=re.MULTILINE)
        block = re.sub(r"^Prepared release tag: .*$", release_tag, block, count=1, flags=re.MULTILINE)
        block = re.sub(r"^Current release tag: .*$", release_tag, block, count=1, flags=re.MULTILINE)
        block = re.sub(r"^Verified Zenodo version DOI: `10\\.5281/zenodo\\.\\d+`\\.", doi_line, block, count=1, flags=re.MULTILINE)
        block = re.sub(
            rf"^{re.escape(tag)} .*?(pending|prepared).*?$",
            f"{tag} GitHub Release publication and post-release Zenodo verification are complete. Verified Zenodo version DOI: `{doi}`.",
            block,
            count=1,
            flags=re.MULTILINE,
        )

    return before + block + after

