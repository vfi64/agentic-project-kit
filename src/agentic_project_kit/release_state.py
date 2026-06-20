from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from agentic_project_kit.post_release_closeout import EXPECTED_DOI_CLOSEOUT_PATHS
from agentic_project_kit.release import CommandResult, run_command


ReleaseStateRunner = Callable[[Path, Sequence[str]], CommandResult]
ReleaseStateHttpGetter = Callable[[str], CommandResult]
ZENODO_DOI_RE = re.compile(r"10\.5281/zenodo\.\d+")


@dataclass(frozen=True)
class ReleaseLifecycleStep:
    id: str
    status: str
    evidence: tuple[str, ...]
    allowed_commands: tuple[str, ...]
    forbidden_commands: tuple[str, ...]
    next_state: str

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "status": self.status,
            "evidence": list(self.evidence),
            "allowed_commands": list(self.allowed_commands),
            "forbidden_commands": list(self.forbidden_commands),
            "next_state": self.next_state,
        }


@dataclass(frozen=True)
class ReleaseLifecycleStatus:
    schema_version: int
    kind: str
    version: str
    result_status: str
    current_state: str
    package_version: str
    init_version: str
    citation_version: str
    concept_doi: str
    version_doi: str
    current_verified_version: str
    current_verified_doi: str
    local_tag_exists: bool
    remote: "RemoteReleaseStatus"
    steps: tuple[ReleaseLifecycleStep, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    next_action: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "version": self.version,
            "result_status": self.result_status,
            "current_state": self.current_state,
            "package_version": self.package_version,
            "init_version": self.init_version,
            "citation_version": self.citation_version,
            "concept_doi": self.concept_doi,
            "version_doi": self.version_doi,
            "current_verified_version": self.current_verified_version,
            "current_verified_doi": self.current_verified_doi,
            "local_tag_exists": self.local_tag_exists,
            "remote": self.remote.as_dict(),
            "steps": [step.as_dict() for step in self.steps],
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "next_action": self.next_action,
        }


@dataclass(frozen=True)
class RemoteReleaseStatus:
    status: str
    checked: bool
    local_tag_exists: bool
    remote_tag_exists: bool | None
    github_release_exists: bool | None
    github_release_tag_matches: bool | None
    zenodo_concept_doi_verified: bool | None
    zenodo_version_doi_verified: bool | None
    doi_metadata_version_matches: bool | None
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "checked": self.checked,
            "local_tag_exists": self.local_tag_exists,
            "remote_tag_exists": self.remote_tag_exists,
            "github_release_exists": self.github_release_exists,
            "github_release_tag_matches": self.github_release_tag_matches,
            "zenodo_concept_doi_verified": self.zenodo_concept_doi_verified,
            "zenodo_version_doi_verified": self.zenodo_version_doi_verified,
            "doi_metadata_version_matches": self.doi_metadata_version_matches,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
        }


def build_release_lifecycle_status(
    project_root: Path,
    *,
    version: str | None = None,
    command_runner: ReleaseStateRunner | None = None,
    include_remote: bool = False,
    http_getter: ReleaseStateHttpGetter | None = None,
) -> ReleaseLifecycleStatus:
    runner = command_runner or run_command
    package_version = _read_pyproject_version(project_root)
    init_version = _read_init_version(project_root)
    citation_text = _read(project_root, "CITATION.cff")
    citation_version = _match(r"^version:\s*([^\s]+)", citation_text)
    concept_doi = _match(r"^doi:\s*['\"]?([^'\"\s]+)", citation_text)
    resolved_version = (version or package_version).removeprefix("v")
    verified_releases = _read(project_root, "docs/releases/VERIFIED_RELEASES.md")
    readme = _read(project_root, "README.md")
    changelog = _read(project_root, "CHANGELOG.md")
    current_verified_version, current_verified_doi = _current_verified_from_readme(readme)
    version_doi = _version_doi_from_verified_releases(verified_releases, resolved_version)
    local_tag_exists = _tag_exists(project_root, resolved_version, runner)
    prepared = _is_prepared(
        version=resolved_version,
        package_version=package_version,
        init_version=init_version,
        citation_version=citation_version,
        changelog=changelog,
    )
    closed_out = _is_closed_out(project_root, resolved_version, version_doi)
    current_verified = current_verified_version == resolved_version and current_verified_doi == version_doi and bool(version_doi)
    remote = _remote_release_status(
        project_root,
        version=resolved_version,
        concept_doi=concept_doi,
        version_doi=version_doi,
        local_tag_exists=local_tag_exists,
        include_remote=include_remote,
        runner=runner,
        http_getter=http_getter or _http_get,
    )
    blockers = _blockers(
        package_version=package_version,
        init_version=init_version,
        citation_version=citation_version,
        concept_doi=concept_doi,
        version=resolved_version,
        version_doi=version_doi,
        current_verified_version=current_verified_version,
        current_verified_doi=current_verified_doi,
    ) + remote.blockers
    warnings = (
        _warnings(prepared=prepared, local_tag_exists=local_tag_exists, version_doi=version_doi, closed_out=closed_out)
        + (remote.warnings if remote.checked else ())
    )
    steps = _steps(
        version=resolved_version,
        prepared=prepared,
        local_tag_exists=local_tag_exists,
        version_doi=version_doi,
        closed_out=closed_out,
        current_verified=current_verified,
    )
    current_state = _current_state(steps)
    result_status = "BLOCK" if blockers else ("PASS" if current_state == "current_verified" else "READY")
    return ReleaseLifecycleStatus(
        schema_version=1,
        kind="release_lifecycle_status",
        version=resolved_version,
        result_status=result_status,
        current_state=current_state,
        package_version=package_version,
        init_version=init_version,
        citation_version=citation_version,
        concept_doi=concept_doi,
        version_doi=version_doi,
        current_verified_version=current_verified_version,
        current_verified_doi=current_verified_doi,
        local_tag_exists=local_tag_exists,
        remote=remote,
        steps=steps,
        blockers=blockers,
        warnings=warnings,
        next_action=_next_action(blockers, current_state),
    )


def render_release_lifecycle_status(status: ReleaseLifecycleStatus) -> str:
    lines = [
        "RELEASE_LIFECYCLE_STATUS",
        f"RESULT_STATUS={status.result_status}",
        f"VERSION={status.version}",
        f"CURRENT_STATE={status.current_state}",
        f"PACKAGE_VERSION={status.package_version}",
        f"INIT_VERSION={status.init_version}",
        f"CITATION_VERSION={status.citation_version}",
        f"CONCEPT_DOI={status.concept_doi or '<missing>'}",
        f"VERSION_DOI={status.version_doi or '<missing>'}",
        f"CURRENT_VERIFIED_VERSION={status.current_verified_version or '<missing>'}",
        f"CURRENT_VERIFIED_DOI={status.current_verified_doi or '<missing>'}",
        f"LOCAL_TAG_EXISTS={str(status.local_tag_exists).lower()}",
        f"REMOTE_STATUS={status.remote.status}",
        f"REMOTE_TAG_EXISTS={_bool_or_unknown(status.remote.remote_tag_exists)}",
        f"GITHUB_RELEASE_EXISTS={_bool_or_unknown(status.remote.github_release_exists)}",
        f"ZENODO_CONCEPT_DOI_VERIFIED={_bool_or_unknown(status.remote.zenodo_concept_doi_verified)}",
        f"ZENODO_VERSION_DOI_VERIFIED={_bool_or_unknown(status.remote.zenodo_version_doi_verified)}",
        f"DOI_METADATA_VERSION_MATCHES={_bool_or_unknown(status.remote.doi_metadata_version_matches)}",
    ]
    for step in status.steps:
        lines.append(f"STEP={step.id}|{step.status}|{step.next_state}")
    for warning in status.warnings:
        lines.append(f"WARNING={warning}")
    for blocker in status.blockers:
        lines.append(f"BLOCKER={blocker}")
    lines.append(f"NEXT={status.next_action}")
    lines.append(f"FINAL_SIGNAL={'f' if status.blockers else 'd'}")
    return "\n".join(lines) + "\n"


def _bool_or_unknown(value: bool | None) -> str:
    if value is None:
        return "not_checked"
    return str(value).lower()


def _read(project_root: Path, relative_path: str) -> str:
    path = project_root / relative_path
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _match(pattern: str, text: str) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _read_pyproject_version(project_root: Path) -> str:
    return _match(r"^version\s*=\s*\"([^\"]+)\"", _read(project_root, "pyproject.toml"))


def _read_init_version(project_root: Path) -> str:
    return _match(r"^__version__\s*=\s*\"([^\"]+)\"", _read(project_root, "src/agentic_project_kit/__init__.py"))


def _current_verified_from_readme(readme: str) -> tuple[str, str]:
    match = re.search(
        r"Current verified release:\s*`?v?([0-9]+(?:\.[0-9]+){2})`?.*?`?(10\.5281/zenodo\.\d+)`?",
        readme,
    )
    return (match.group(1), match.group(2)) if match else ("", "")


def _version_doi_from_verified_releases(text: str, version: str) -> str:
    list_match = re.search(
        rf"(?m)^-\s+`v{re.escape(version)}`\s*/\s*`{re.escape(version)}`:.*?Zenodo version DOI `(?P<doi>10\.5281/zenodo\.\d+)`",
        text,
    )
    if list_match:
        return list_match.group("doi")
    block_match = re.search(rf"(?ms)^##\s+v{re.escape(version)}\b(?P<body>.*?)(?=^##\s+v|\Z)", text)
    if not block_match:
        return ""
    doi_match = ZENODO_DOI_RE.search(block_match.group("body"))
    return doi_match.group(0) if doi_match else ""


def _tag_exists(project_root: Path, version: str, runner: ReleaseStateRunner) -> bool:
    result = runner(project_root, ["git", "rev-parse", "--verify", f"v{version}"])
    return result.returncode == 0


def _remote_release_status(
    project_root: Path,
    *,
    version: str,
    concept_doi: str,
    version_doi: str,
    local_tag_exists: bool,
    include_remote: bool,
    runner: ReleaseStateRunner,
    http_getter: ReleaseStateHttpGetter,
) -> RemoteReleaseStatus:
    if not include_remote:
        return RemoteReleaseStatus(
            status="NOT_CHECKED",
            checked=False,
            local_tag_exists=local_tag_exists,
            remote_tag_exists=None,
            github_release_exists=None,
            github_release_tag_matches=None,
            zenodo_concept_doi_verified=None,
            zenodo_version_doi_verified=None,
            doi_metadata_version_matches=None,
            blockers=(),
            warnings=("remote_checks_not_requested",),
        )

    tag = f"v{version}"
    remote_tag_exists: bool | None = None
    github_release_exists: bool | None = None
    github_release_tag_matches: bool | None = None
    zenodo_concept_doi_verified: bool | None = None
    zenodo_version_doi_verified: bool | None = None
    doi_metadata_version_matches: bool | None = None
    blockers: list[str] = []
    warnings: list[str] = []

    remote_tag = runner(project_root, ["git", "ls-remote", "--tags", "origin", tag])
    if remote_tag.returncode == 0:
        remote_tag_exists = tag in remote_tag.stdout
    else:
        warnings.append("remote_tag_check_inconclusive")

    github_release = runner(project_root, ["gh", "release", "view", tag, "--json", "tagName"])
    if github_release.returncode == 0:
        github_release_exists = True
        github_release_tag_matches = tag in github_release.stdout
    elif github_release.returncode == 1:
        github_release_exists = False
        github_release_tag_matches = False
    else:
        warnings.append("github_release_check_inconclusive")

    if concept_doi:
        zenodo_concept_doi_verified = _doi_http_verified(concept_doi, http_getter)
        if zenodo_concept_doi_verified is None:
            warnings.append("zenodo_concept_doi_check_inconclusive")
    if version_doi:
        version_payload = _zenodo_record_payload(version_doi, http_getter)
        if version_payload is None:
            zenodo_version_doi_verified = None
            doi_metadata_version_matches = None
            warnings.append("zenodo_version_doi_check_inconclusive")
        else:
            zenodo_version_doi_verified = version_doi in version_payload
            doi_metadata_version_matches = version in version_payload

    if local_tag_exists and remote_tag_exists is False:
        blockers.append("remote_tag_missing_for_local_tag")
    if local_tag_exists and github_release_exists is False:
        blockers.append("github_release_missing_for_local_tag")
    if local_tag_exists and github_release_tag_matches is False:
        blockers.append("github_release_tag_mismatch")
    if concept_doi and zenodo_concept_doi_verified is False:
        blockers.append("zenodo_concept_doi_not_verified")
    if version_doi and zenodo_version_doi_verified is False:
        blockers.append("zenodo_version_doi_not_verified")
    if version_doi and doi_metadata_version_matches is False:
        blockers.append("zenodo_version_metadata_mismatch")

    status = "BLOCK" if blockers else ("WARN" if warnings else "PASS")
    return RemoteReleaseStatus(
        status=status,
        checked=True,
        local_tag_exists=local_tag_exists,
        remote_tag_exists=remote_tag_exists,
        github_release_exists=github_release_exists,
        github_release_tag_matches=github_release_tag_matches,
        zenodo_concept_doi_verified=zenodo_concept_doi_verified,
        zenodo_version_doi_verified=zenodo_version_doi_verified,
        doi_metadata_version_matches=doi_metadata_version_matches,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
    )


def _doi_http_verified(doi: str, http_getter: ReleaseStateHttpGetter) -> bool | None:
    result = http_getter(f"https://doi.org/{doi}")
    if result.returncode == 0:
        return True
    if result.returncode == 404:
        return False
    return None


def _zenodo_record_payload(doi: str, http_getter: ReleaseStateHttpGetter) -> str | None:
    record_id = doi.rsplit(".", 1)[-1]
    result = http_getter(f"https://zenodo.org/api/records/{record_id}")
    if result.returncode != 0:
        return None
    return result.stdout


def _http_get(url: str) -> CommandResult:
    request = Request(url, headers={"User-Agent": "agentic-project-kit/release-status"})
    try:
        with urlopen(request, timeout=10) as response:
            return CommandResult(0, response.read().decode("utf-8", errors="replace"), "")
    except HTTPError as exc:
        return CommandResult(exc.code, "", str(exc))
    except URLError as exc:
        return CommandResult(2, "", str(exc))


def _is_prepared(
    *,
    version: str,
    package_version: str,
    init_version: str,
    citation_version: str,
    changelog: str,
) -> bool:
    return (
        package_version == version
        and init_version == version
        and citation_version == version
        and bool(re.search(rf"(?m)^##\s+v{re.escape(version)}\b", changelog))
    )


def _is_closed_out(project_root: Path, version: str, version_doi: str) -> bool:
    if not version_doi:
        return False
    for relative_path in EXPECTED_DOI_CLOSEOUT_PATHS:
        text = _read(project_root, relative_path)
        if version not in text or version_doi not in text:
            return False
    return True


def _blockers(
    *,
    package_version: str,
    init_version: str,
    citation_version: str,
    concept_doi: str,
    version: str,
    version_doi: str,
    current_verified_version: str,
    current_verified_doi: str,
) -> tuple[str, ...]:
    blockers: list[str] = []
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        blockers.append("invalid_target_version")
    if package_version != init_version:
        blockers.append("package_init_version_mismatch")
    if citation_version and citation_version != package_version:
        blockers.append("citation_version_mismatch")
    if concept_doi and not concept_doi.startswith("10.5281/zenodo."):
        blockers.append("concept_doi_not_zenodo")
    if current_verified_version == version and current_verified_doi != version_doi:
        blockers.append("current_verified_doi_mismatch")
    return tuple(blockers)


def _warnings(*, prepared: bool, local_tag_exists: bool, version_doi: str, closed_out: bool) -> tuple[str, ...]:
    warnings: list[str] = []
    if prepared and not local_tag_exists:
        warnings.append("prepared_but_not_published")
    if local_tag_exists and not version_doi:
        warnings.append("published_but_doi_not_closed_out")
    if version_doi and not closed_out:
        warnings.append("doi_present_but_closeout_incomplete")
    return tuple(warnings)


def _steps(
    *,
    version: str,
    prepared: bool,
    local_tag_exists: bool,
    version_doi: str,
    closed_out: bool,
    current_verified: bool,
) -> tuple[ReleaseLifecycleStep, ...]:
    return (
        ReleaseLifecycleStep(
            "planned",
            "PASS",
            (f"target_version={version}",),
            ("agentic-kit release-preflight --version <version>",),
            ("release-publish", "post-release-doi-closeout --write"),
            "prepared",
        ),
        ReleaseLifecycleStep(
            "prepared",
            "PASS" if prepared else "PENDING",
            (f"metadata_prepared={prepared}",),
            (
                "agentic-kit release-prep --version <version> --summary-line <line> --json",
                "agentic-kit release-check --version <version>",
            ),
            ("manual release metadata patching",),
            "published",
        ),
        ReleaseLifecycleStep(
            "published",
            "PASS" if local_tag_exists else "PENDING",
            (f"local_tag_exists={local_tag_exists}",),
            ("agentic-kit release-publish --version <version> --dry-run --json", "agentic-kit release-publish --version <version> --execute --allow-execute --json"),
            ("post-release-doi-closeout --write before post-release-check PASS",),
            "doi_verified",
        ),
        ReleaseLifecycleStep(
            "doi_verified",
            "PASS" if version_doi else "PENDING",
            ((f"version_doi={version_doi}",) if version_doi else ("version_doi=<missing>",)),
            ("agentic-kit post-release-check --version <version>",),
            ("manual DOI metadata edits",),
            "closed_out",
        ),
        ReleaseLifecycleStep(
            "closed_out",
            "PASS" if closed_out else "PENDING",
            (f"expected_paths={len(EXPECTED_DOI_CLOSEOUT_PATHS)}",),
            ("agentic-kit post-release-doi-closeout --version <version> --write --json",),
            ("partial DOI closeout commit",),
            "current_verified",
        ),
        ReleaseLifecycleStep(
            "current_verified",
            "PASS" if current_verified else "PENDING",
            (f"current_verified={current_verified}",),
            ("agentic-kit transfer post-merge-check", "agentic-kit transfer repo-status"),
            ("GUI work before final release handoff",),
            "done",
        ),
    )


def _current_state(steps: tuple[ReleaseLifecycleStep, ...]) -> str:
    latest = "planned"
    for step in steps:
        if step.status == "PASS":
            latest = step.id
        else:
            break
    return latest


def _next_action(blockers: tuple[str, ...], current_state: str) -> str:
    if blockers:
        return "Resolve release-state blockers before continuing: " + ", ".join(blockers)
    mapping = {
        "planned": "Run release-prep through the supported agentic-kit route.",
        "prepared": "Run release-publish dry-run and then guarded execute when ready.",
        "published": "Run post-release-check until DOI verification is PASS.",
        "doi_verified": "Run post-release-doi-closeout --write and commit the full expected file set.",
        "closed_out": "Merge closeout and refresh handoff until current_verified is PASS.",
        "current_verified": "Release lifecycle is closed out; next planning slice may proceed.",
    }
    return mapping.get(current_state, "Inspect release lifecycle status.")
