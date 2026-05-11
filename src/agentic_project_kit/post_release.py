from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json
import re
import urllib.parse
import urllib.request

from agentic_project_kit.release import CommandResult, read_project_version, run_command

ZENODO_HTTP_TIMEOUT_SECONDS = 5


class PostReleaseStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    WAITING = "WAITING"


@dataclass(frozen=True)
class PostReleaseCheckResult:
    name: str
    status: PostReleaseStatus
    detail: str


@dataclass(frozen=True)
class PostReleaseReport:
    version: str
    checks: tuple[PostReleaseCheckResult, ...]

    @property
    def ok(self) -> bool:
        return all(check.status != PostReleaseStatus.FAIL for check in self.checks)


HttpGetter = Callable[[str], tuple[int, str]]
CommandRunner = Callable[[Path, Sequence[str]], CommandResult]


def build_post_release_report(
    project_root: Path,
    version: str | None = None,
    command_runner: CommandRunner | None = None,
    http_getter: HttpGetter | None = None,
) -> PostReleaseReport:
    resolved_version = version or read_project_version(project_root)
    resolved_command_runner = command_runner or run_command
    resolved_http_getter = http_getter or urlopen_text

    github_release = check_github_release_exists(project_root, resolved_version, resolved_command_runner)
    concept_doi = read_citation_doi(project_root)
    concept_doi_check = check_concept_doi(concept_doi)
    zenodo_check = check_zenodo_version_record(resolved_version, concept_doi, resolved_http_getter)

    return PostReleaseReport(
        version=resolved_version,
        checks=(github_release, concept_doi_check, zenodo_check),
    )


def check_github_release_exists(
    project_root: Path,
    version: str,
    command_runner: CommandRunner | None = None,
) -> PostReleaseCheckResult:
    resolved_command_runner = command_runner or run_command
    tag = f"v{version}"
    result = resolved_command_runner(project_root, ["gh", "release", "view", tag])
    output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
    if result.returncode == 0:
        return PostReleaseCheckResult("GitHub release", PostReleaseStatus.PASS, f"GitHub release exists: {tag}")
    if result.returncode == 127 or _looks_like_unavailable_github_cli(output):
        return PostReleaseCheckResult("GitHub release", PostReleaseStatus.WARN, output or "gh release view failed")
    if _looks_like_missing_github_release(output):
        return PostReleaseCheckResult("GitHub release", PostReleaseStatus.FAIL, f"GitHub release is absent: {tag}")
    return PostReleaseCheckResult("GitHub release", PostReleaseStatus.WARN, output or "gh release view failed")


def check_concept_doi(concept_doi: str | None) -> PostReleaseCheckResult:
    if not concept_doi:
        return PostReleaseCheckResult(
            "Zenodo concept DOI",
            PostReleaseStatus.WARN,
            "no DOI found in CITATION.cff; Zenodo lookup skipped",
        )
    if not concept_doi.startswith("10.5281/zenodo."):
        return PostReleaseCheckResult(
            "Zenodo concept DOI",
            PostReleaseStatus.WARN,
            f"DOI does not look like a Zenodo DOI: {concept_doi}",
        )
    return PostReleaseCheckResult("Zenodo concept DOI", PostReleaseStatus.PASS, f"found DOI: {concept_doi}")


def check_zenodo_version_record(
    version: str,
    concept_doi: str | None,
    http_getter: HttpGetter | None = None,
) -> PostReleaseCheckResult:
    if not concept_doi:
        return PostReleaseCheckResult(
            "Zenodo version DOI",
            PostReleaseStatus.WARN,
            "Zenodo lookup skipped because no concept DOI was found",
        )

    resolved_http_getter = http_getter or urlopen_text
    url = build_zenodo_records_url(concept_doi)
    try:
        status_code, body = resolved_http_getter(url)
    except OSError as exc:
        return PostReleaseCheckResult("Zenodo version DOI", PostReleaseStatus.WARN, f"Zenodo lookup failed: {exc}")

    if status_code != 200:
        return PostReleaseCheckResult(
            "Zenodo version DOI",
            PostReleaseStatus.WARN,
            f"Zenodo lookup returned HTTP {status_code}",
        )

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        return PostReleaseCheckResult("Zenodo version DOI", PostReleaseStatus.WARN, f"Zenodo JSON parse failed: {exc}")

    version_doi = find_version_doi(payload, version)
    if version_doi:
        return PostReleaseCheckResult(
            "Zenodo version DOI",
            PostReleaseStatus.PASS,
            f"verified version DOI for v{version}: {version_doi}",
        )

    return PostReleaseCheckResult(
        "Zenodo version DOI",
        PostReleaseStatus.WAITING,
        f"no verified Zenodo record found yet for v{version}; leave README/CITATION unchanged",
    )


def build_zenodo_records_url(concept_doi: str) -> str:
    query = f'conceptdoi:"{concept_doi}"'
    return "https://zenodo.org/api/records?" + urllib.parse.urlencode(
        {"q": query, "all_versions": "true", "sort": "mostrecent"}
    )


def find_version_doi(payload: object, version: str) -> str | None:
    hits = _extract_hits(payload)
    wanted = {version, f"v{version}"}
    for record in hits:
        if not isinstance(record, dict):
            continue
        metadata = record.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        record_version = str(metadata.get("version", "")).strip()
        title = str(metadata.get("title", ""))
        doi = str(record.get("doi") or metadata.get("doi") or "").strip()
        if not doi:
            continue
        if record_version in wanted or _title_mentions_version(title, version):
            return doi
    return None


def read_citation_doi(project_root: Path) -> str | None:
    citation = project_root / "CITATION.cff"
    if not citation.exists():
        return None
    match = re.search(r"^doi:\s*['\"]?([^'\"\s]+)", citation.read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip()


def render_post_release_report(report: PostReleaseReport) -> str:
    lines = [f"Post-release check for target v{report.version}", ""]
    for check in report.checks:
        lines.append(f"[{check.status.value}] {check.name}: {check.detail}")
    lines.append("")
    lines.append("Overall: PASS" if report.ok else "Overall: FAIL")
    return "\n".join(lines) + "\n"


def urlopen_text(url: str) -> tuple[int, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "agentic-project-kit"})
    with urllib.request.urlopen(request, timeout=ZENODO_HTTP_TIMEOUT_SECONDS) as response:  # noqa: S310
        status = getattr(response, "status", 200)
        body = response.read().decode("utf-8")
    return status, body


def _extract_hits(payload: object) -> list[object]:
    if not isinstance(payload, dict):
        return []
    hits = payload.get("hits")
    if isinstance(hits, dict):
        records = hits.get("hits")
        if isinstance(records, list):
            return records
    if isinstance(hits, list):
        return hits
    return []


def _title_mentions_version(title: str, version: str) -> bool:
    normalized = title.lower()
    return f"v{version}" in normalized or f" {version}" in normalized


def _looks_like_unavailable_github_cli(output: str) -> bool:
    normalized = output.lower()
    return any(fragment in normalized for fragment in ("could not run gh", "gh unavailable"))


def _looks_like_missing_github_release(output: str) -> bool:
    normalized = output.lower()
    return any(fragment in normalized for fragment in ("release not found", "http 404"))
