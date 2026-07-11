from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from types import MappingProxyType


@dataclass(frozen=True)
class PathLiteralPattern:
    name: str
    literal: str


PATH_LITERAL_PATTERNS = (
    PathLiteralPattern("quoted_docs", '"' + 'docs/'),
    PathLiteralPattern("path_docs", 'Path(' + '"' + 'docs'),
    PathLiteralPattern("quoted_tmp", '"' + 'tmp/'),
    PathLiteralPattern("path_tmp", 'Path(' + '"' + 'tmp'),
)

REPO_IDENTITY_PATTERNS = (
    PathLiteralPattern("repo_slug_prefix", "vfi64/"),
    PathLiteralPattern("github_url", "github.com/"),
)


@dataclass(frozen=True)
class PathLiteralClassification:
    kind: str
    counts_as_active_path_literal: bool
    rationale: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RepoIdentityLiteralClassification:
    kind: str
    counts_as_active_identity_literal: bool
    rationale: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


DECLARED_PATH_LITERAL_CLASSIFICATIONS = MappingProxyType(
    {
        "src/agentic_project_kit/workspace.py": PathLiteralClassification(
            kind="resolver_source",
            counts_as_active_path_literal=False,
            rationale="workspace.py is the declared single source for legacy and namespace path defaults",
        ),
        "src/agentic_project_kit/templates.py": PathLiteralClassification(
            kind="template_data",
            counts_as_active_path_literal=False,
            rationale="generated project template contents are data, not kit runtime path access",
        ),
    }
)

DECLARED_REPO_IDENTITY_EXCEPTIONS = MappingProxyType(
    {
        "src/agentic_project_kit/gui_cockpit_actions.py": RepoIdentityLiteralClassification(
            kind="reference",
            counts_as_active_identity_literal=False,
            rationale="GUI help text points users to the kit source repository; it is not runtime workspace identity",
        ),
        "src/agentic_project_kit/gui_task_editor.py": RepoIdentityLiteralClassification(
            kind="template",
            counts_as_active_identity_literal=False,
            rationale="GUI initial-prompt template is fixed kit bootstrap copy until P6 parameterizes selected workspaces",
        ),
        "src/agentic_project_kit/templates.py": RepoIdentityLiteralClassification(
            kind="template",
            counts_as_active_identity_literal=False,
            rationale="generated project template contents are data and package metadata, not runtime repository identity",
        ),
    }
)


@dataclass(frozen=True)
class PathLiteralModuleCount:
    path: str
    total: int
    patterns: dict[str, int]
    classification: PathLiteralClassification

    def as_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["classification"] = self.classification.as_dict()
        return data


@dataclass(frozen=True)
class RepoIdentityLiteralModuleCount:
    path: str
    total: int
    patterns: dict[str, int]
    classification: RepoIdentityLiteralClassification

    def as_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["classification"] = self.classification.as_dict()
        return data


@dataclass(frozen=True)
class PathLiteralAuditResult:
    root: str
    patterns: tuple[PathLiteralPattern, ...]
    modules: tuple[PathLiteralModuleCount, ...]
    repo_identity_patterns: tuple[PathLiteralPattern, ...]
    repo_identity_modules: tuple[RepoIdentityLiteralModuleCount, ...]

    @property
    def status(self) -> str:
        return "REPORT"

    @property
    def returncode(self) -> int:
        return 0

    @property
    def affected_module_count(self) -> int:
        return len(self.modules)

    @property
    def literal_count(self) -> int:
        return sum(module.total for module in self.modules)

    @property
    def active_path_modules(self) -> tuple[PathLiteralModuleCount, ...]:
        return tuple(
            module
            for module in self.modules
            if module.classification.counts_as_active_path_literal
        )

    @property
    def active_path_module_count(self) -> int:
        return len(self.active_path_modules)

    @property
    def active_path_literal_count(self) -> int:
        return sum(module.total for module in self.active_path_modules)

    @property
    def declared_exception_modules(self) -> tuple[PathLiteralModuleCount, ...]:
        return tuple(
            module
            for module in self.modules
            if module.classification.kind in {"resolver_source", "template_data"}
        )

    @property
    def repo_identity_literal_count(self) -> int:
        return sum(module.total for module in self.repo_identity_modules)

    @property
    def active_repo_identity_modules(self) -> tuple[RepoIdentityLiteralModuleCount, ...]:
        return tuple(
            module
            for module in self.repo_identity_modules
            if module.classification.counts_as_active_identity_literal
        )

    @property
    def active_repo_identity_module_count(self) -> int:
        return len(self.active_repo_identity_modules)

    @property
    def active_repo_identity_literal_count(self) -> int:
        return sum(module.total for module in self.active_repo_identity_modules)

    @property
    def declared_identity_exception_modules(self) -> tuple[RepoIdentityLiteralModuleCount, ...]:
        return tuple(
            module
            for module in self.repo_identity_modules
            if module.path in DECLARED_REPO_IDENTITY_EXCEPTIONS
        )

    @property
    def classification_summary(self) -> dict[str, dict[str, object]]:
        summary: dict[str, dict[str, object]] = {}
        for module in self.modules:
            classification = module.classification
            entry = summary.setdefault(
                classification.kind,
                {
                    "module_count": 0,
                    "literal_count": 0,
                    "counts_as_active_path_literal": classification.counts_as_active_path_literal,
                },
            )
            entry["module_count"] = int(entry["module_count"]) + 1
            entry["literal_count"] = int(entry["literal_count"]) + module.total
        return dict(sorted(summary.items()))

    @property
    def repo_identity_classification_summary(self) -> dict[str, dict[str, object]]:
        summary: dict[str, dict[str, object]] = {}
        for module in self.repo_identity_modules:
            classification = module.classification
            entry = summary.setdefault(
                classification.kind,
                {
                    "module_count": 0,
                    "literal_count": 0,
                    "counts_as_active_identity_literal": classification.counts_as_active_identity_literal,
                },
            )
            entry["module_count"] = int(entry["module_count"]) + 1
            entry["literal_count"] = int(entry["literal_count"]) + module.total
        return dict(sorted(summary.items()))

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "path_literal_audit",
            "root": self.root,
            "status": self.status,
            "affected_module_count": self.affected_module_count,
            "literal_count": self.literal_count,
            "active_path_module_count": self.active_path_module_count,
            "active_path_literal_count": self.active_path_literal_count,
            "declared_exception_module_count": len(self.declared_exception_modules),
            "classification_summary": self.classification_summary,
            "patterns": [asdict(pattern) for pattern in self.patterns],
            "modules": [module.as_dict() for module in self.modules],
            "active_path_modules": [module.as_dict() for module in self.active_path_modules],
            "declared_exception_modules": [
                module.as_dict() for module in self.declared_exception_modules
            ],
            "repo_identity_literal_count": self.repo_identity_literal_count,
            "active_repo_identity_module_count": self.active_repo_identity_module_count,
            "active_repo_identity_literal_count": self.active_repo_identity_literal_count,
            "declared_identity_exception_module_count": len(
                self.declared_identity_exception_modules
            ),
            "repo_identity_classification_summary": self.repo_identity_classification_summary,
            "repo_identity_patterns": [asdict(pattern) for pattern in self.repo_identity_patterns],
            "repo_identity_modules": [
                module.as_dict() for module in self.repo_identity_modules
            ],
            "active_repo_identity_modules": [
                module.as_dict() for module in self.active_repo_identity_modules
            ],
            "declared_identity_exception_modules": [
                module.as_dict() for module in self.declared_identity_exception_modules
            ],
        }


@dataclass(frozen=True)
class PathLiteralActiveClassEnforcementResult:
    audit: PathLiteralAuditResult

    @property
    def status(self) -> str:
        return "PASS" if self.blocker_count == 0 else "FAIL"

    @property
    def returncode(self) -> int:
        return 0 if self.status == "PASS" else 1

    @property
    def blocker_count(self) -> int:
        return self.audit.active_path_module_count + self.audit.active_repo_identity_module_count

    @property
    def active_path_literal_count(self) -> int:
        return self.audit.active_path_literal_count

    @property
    def active_identity_literal_count(self) -> int:
        return self.audit.active_repo_identity_literal_count

    @property
    def non_blocking_path_literal_count(self) -> int:
        return self.audit.literal_count - self.audit.active_path_literal_count

    @property
    def non_blocking_identity_literal_count(self) -> int:
        return self.audit.repo_identity_literal_count - self.audit.active_repo_identity_literal_count

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "path_literal_active_class_enforcement",
            "status": self.status,
            "returncode": self.returncode,
            "blocker_count": self.blocker_count,
            "active_path_literal_count": self.active_path_literal_count,
            "active_identity_literal_count": self.active_identity_literal_count,
            "non_blocking_path_literal_count": self.non_blocking_path_literal_count,
            "non_blocking_identity_literal_count": self.non_blocking_identity_literal_count,
            "active_path_modules": [
                module.as_dict() for module in self.audit.active_path_modules
            ],
            "active_identity_modules": [
                module.as_dict() for module in self.audit.active_repo_identity_modules
            ],
            "audit": self.audit.as_dict(),
        }


def audit_path_literals(
    root: Path = Path("."),
    *,
    patterns: tuple[PathLiteralPattern, ...] = PATH_LITERAL_PATTERNS,
    repo_identity_patterns: tuple[PathLiteralPattern, ...] = REPO_IDENTITY_PATTERNS,
) -> PathLiteralAuditResult:
    root = root.resolve()
    modules: list[PathLiteralModuleCount] = []
    repo_identity_modules: list[RepoIdentityLiteralModuleCount] = []
    src_root = root / "src"
    if src_root.exists():
        for path in sorted(src_root.rglob("*.py")):
            if not path.is_file() or path.is_symlink():
                continue
            relative_path = path.relative_to(root).as_posix()
            counts = _count_path_literals(path, patterns)
            total = sum(counts.values())
            if total:
                modules.append(
                    PathLiteralModuleCount(
                        path=relative_path,
                        total=total,
                        patterns=counts,
                        classification=_classify_path_literal_module(relative_path, counts),
                    )
                )
            if relative_path != "src/agentic_project_kit/path_literal_audit.py":
                repo_identity_counts = _count_path_literals(path, repo_identity_patterns)
                repo_identity_total = sum(repo_identity_counts.values())
                if repo_identity_total:
                    repo_identity_modules.append(
                        RepoIdentityLiteralModuleCount(
                            path=relative_path,
                            total=repo_identity_total,
                            patterns=repo_identity_counts,
                            classification=_classify_repo_identity_literal_module(
                                relative_path,
                                repo_identity_counts,
                            ),
                        )
                    )

    modules.sort(key=lambda module: (-module.total, module.path))
    repo_identity_modules.sort(key=lambda module: (-module.total, module.path))
    return PathLiteralAuditResult(
        root=root.as_posix(),
        patterns=patterns,
        modules=tuple(modules),
        repo_identity_patterns=repo_identity_patterns,
        repo_identity_modules=tuple(repo_identity_modules),
    )


def enforce_active_literal_classes(
    result: PathLiteralAuditResult,
) -> PathLiteralActiveClassEnforcementResult:
    return PathLiteralActiveClassEnforcementResult(audit=result)


def render_path_literal_audit(result: PathLiteralAuditResult) -> str:
    lines = [
        "PATH_LITERAL_AUDIT",
        f"STATUS={result.status}",
        f"AFFECTED_MODULES={result.affected_module_count}",
        f"LITERAL_COUNT={result.literal_count}",
        f"ACTIVE_PATH_MODULES={result.active_path_module_count}",
        f"ACTIVE_PATH_LITERAL_COUNT={result.active_path_literal_count}",
        f"DECLARED_EXCEPTION_MODULES={len(result.declared_exception_modules)}",
        f"REPO_IDENTITY_MODULES={len(result.repo_identity_modules)}",
        f"REPO_IDENTITY_LITERAL_COUNT={result.repo_identity_literal_count}",
        f"ACTIVE_IDENTITY_MODULES={result.active_repo_identity_module_count}",
        f"ACTIVE_IDENTITY_LITERAL_COUNT={result.active_repo_identity_literal_count}",
        f"DECLARED_IDENTITY_EXCEPTION_MODULES={len(result.declared_identity_exception_modules)}",
    ]
    if result.classification_summary:
        lines.append("CLASSIFICATION_SUMMARY:")
        for kind, summary in result.classification_summary.items():
            disposition = "active" if summary["counts_as_active_path_literal"] else "non-active"
            lines.append(
                f"- {kind}: modules={summary['module_count']} literals={summary['literal_count']} "
                f"disposition={disposition}"
            )
    for module in result.modules:
        pattern_summary = "|".join(
            f"{pattern.name}={module.patterns.get(pattern.name, 0)}"
            for pattern in result.patterns
        )
        disposition = "active" if module.classification.counts_as_active_path_literal else "non-active"
        lines.append(
            f"MODULE={module.total}|{module.path}|classification={module.classification.kind}|"
            f"disposition={disposition}|{pattern_summary}"
        )
    if result.declared_exception_modules:
        lines.append("DECLARED_EXCEPTIONS:")
        for module in result.declared_exception_modules:
            lines.append(
                f"- {module.path}: {module.classification.kind} — {module.classification.rationale}"
            )
    if result.repo_identity_modules:
        lines.append("REPO_IDENTITY_LITERALS:")
        for module in result.repo_identity_modules:
            pattern_summary = "|".join(
                f"{pattern.name}={module.patterns.get(pattern.name, 0)}"
                for pattern in result.repo_identity_patterns
            )
            disposition = (
                "active" if module.classification.counts_as_active_identity_literal else "non-active"
            )
            lines.append(
                f"REPO_IDENTITY={module.total}|{module.path}|classification={module.classification.kind}|"
                f"disposition={disposition}|{pattern_summary}"
            )
    if result.declared_identity_exception_modules:
        lines.append("DECLARED_IDENTITY_EXCEPTIONS:")
        for module in result.declared_identity_exception_modules:
            lines.append(
                f"- {module.path}: {module.classification.kind} — {module.classification.rationale}"
            )
    return "\n".join(lines) + "\n"


def render_path_literal_active_class_enforcement(
    result: PathLiteralActiveClassEnforcementResult,
) -> str:
    lines = [
        "PATH_LITERAL_ACTIVE_CLASS_ENFORCEMENT",
        f"STATUS={result.status}",
        f"BLOCKER_COUNT={result.blocker_count}",
        f"ACTIVE_PATH_LITERAL_COUNT={result.active_path_literal_count}",
        f"ACTIVE_IDENTITY_LITERAL_COUNT={result.active_identity_literal_count}",
        f"NON_BLOCKING_PATH_LITERAL_COUNT={result.non_blocking_path_literal_count}",
        f"NON_BLOCKING_IDENTITY_LITERAL_COUNT={result.non_blocking_identity_literal_count}",
    ]
    for module in result.audit.active_path_modules:
        lines.append(
            f"BLOCKER=active_path_literal|{module.path}|literals={module.total}|"
            f"classification={module.classification.kind}"
        )
    for module in result.audit.active_repo_identity_modules:
        lines.append(
            f"BLOCKER=active_identity_literal|{module.path}|literals={module.total}|"
            f"classification={module.classification.kind}"
        )
    if result.audit.modules:
        lines.append("PATH_LITERAL_CLASSIFICATION_SUMMARY:")
        for kind, summary in result.audit.classification_summary.items():
            disposition = "active" if summary["counts_as_active_path_literal"] else "non-active"
            lines.append(
                f"- {kind}: modules={summary['module_count']} literals={summary['literal_count']} "
                f"disposition={disposition}"
            )
    if result.audit.repo_identity_modules:
        lines.append("REPO_IDENTITY_CLASSIFICATION_SUMMARY:")
        for kind, summary in result.audit.repo_identity_classification_summary.items():
            disposition = (
                "active" if summary["counts_as_active_identity_literal"] else "non-active"
            )
            lines.append(
                f"- {kind}: modules={summary['module_count']} literals={summary['literal_count']} "
                f"disposition={disposition}"
            )
    return "\n".join(lines) + "\n"


def render_path_literal_evidence_report(
    result: PathLiteralAuditResult,
    *,
    command: str = "agentic-kit audit-path-literals",
    generated_on: date | None = None,
) -> str:
    generated = generated_on or date.today()
    pattern_headers = [pattern.name for pattern in result.patterns]
    lines = [
        "# Path Literal Audit Evidence",
        "",
        f"Generated: {generated.isoformat()}",
        f"Command: `{command}`",
        "Mode: REPORT-ONLY; this evidence does not gate the standard suite.",
        "",
        f"Affected modules: {result.affected_module_count}",
        f"Literal count: {result.literal_count}",
        f"Active path modules: {result.active_path_module_count}",
        f"Active path literal count: {result.active_path_literal_count}",
        f"Declared exception modules: {len(result.declared_exception_modules)}",
        "",
        "## Path Literal Classifications",
        "",
        "| module | classification | disposition | total | " + " | ".join(pattern_headers) + " |",
        "|---|---|---|---:|" + "|".join("---:" for _ in pattern_headers) + "|",
    ]
    for module in result.modules:
        counts = [str(module.patterns.get(name, 0)) for name in pattern_headers]
        disposition = "active" if module.classification.counts_as_active_path_literal else "non-active"
        lines.append(
            f"| {module.path} | {module.classification.kind} | {disposition} | {module.total} | "
            + " | ".join(counts)
            + " |"
        )
    lines.extend(["", "## Declared Exceptions", ""])
    if result.declared_exception_modules:
        for module in result.declared_exception_modules:
            lines.append(
                f"- `{module.path}`: `{module.classification.kind}` — {module.classification.rationale}"
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Repo Identity Literals",
            "",
            "Repo identity literals are listed for follow-up visibility and are not migrated by P4b.",
            "",
            f"Repo identity literal count: {result.repo_identity_literal_count}",
            f"Active repo identity modules: {result.active_repo_identity_module_count}",
            f"Active repo identity literal count: {result.active_repo_identity_literal_count}",
            "",
        ]
    )
    repo_pattern_headers = [pattern.name for pattern in result.repo_identity_patterns]
    lines.append(
        "| module | classification | disposition | total | "
        + " | ".join(repo_pattern_headers)
        + " |"
    )
    lines.append("|---|---|---|---:|" + "|".join("---:" for _ in repo_pattern_headers) + "|")
    for module in result.repo_identity_modules:
        counts = [str(module.patterns.get(name, 0)) for name in repo_pattern_headers]
        disposition = (
            "active" if module.classification.counts_as_active_identity_literal else "non-active"
        )
        lines.append(
            f"| {module.path} | {module.classification.kind} | {disposition} | {module.total} | "
            + " | ".join(counts)
            + " |"
        )
    if not result.repo_identity_modules:
        lines.append(
            "| none | none | non-active | 0 | "
            + " | ".join("0" for _ in repo_pattern_headers)
            + " |"
        )
    lines.extend(["", "## Declared Identity Exceptions", ""])
    if result.declared_identity_exception_modules:
        for module in result.declared_identity_exception_modules:
            lines.append(
                f"- `{module.path}`: `{module.classification.kind}` — {module.classification.rationale}"
            )
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def _classify_path_literal_module(
    relative_path: str,
    counts: dict[str, int],
) -> PathLiteralClassification:
    declared = DECLARED_PATH_LITERAL_CLASSIFICATIONS.get(relative_path)
    if declared is not None:
        return declared
    if counts.get("path_docs", 0) or counts.get("path_tmp", 0):
        return PathLiteralClassification(
            kind="active_path_literal",
            counts_as_active_path_literal=True,
            rationale="module still constructs docs/tmp paths directly instead of using the workspace resolver",
        )
    return PathLiteralClassification(
        kind="reference_or_message",
        counts_as_active_path_literal=False,
        rationale="quoted docs/tmp text is report, policy, prompt, or diagnostic vocabulary rather than direct Path construction",
    )


def _classify_repo_identity_literal_module(
    relative_path: str,
    counts: dict[str, int],
) -> RepoIdentityLiteralClassification:
    declared = DECLARED_REPO_IDENTITY_EXCEPTIONS.get(relative_path)
    if declared is not None:
        return declared
    if relative_path.endswith("templates.py") or "template" in relative_path:
        return RepoIdentityLiteralClassification(
            kind="template",
            counts_as_active_identity_literal=False,
            rationale="repository identity literal appears in generated template data",
        )
    return RepoIdentityLiteralClassification(
        kind="active",
        counts_as_active_identity_literal=True,
        rationale="repository identity literal is not declared as reference or template data",
    )


def _count_path_literals(
    path: Path,
    patterns: tuple[PathLiteralPattern, ...],
) -> dict[str, int]:
    text = path.read_text(encoding="utf-8")
    return {
        pattern.name: text.count(pattern.literal)
        for pattern in patterns
    }
