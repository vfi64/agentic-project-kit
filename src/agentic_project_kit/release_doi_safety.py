from __future__ import annotations

import re

CONCEPT_DOI = "10.5281/zenodo.20101359"

def extract_verified_version_doi(text: str, version: str) -> str | None:
    """Return only the verified version-specific DOI for a release.

    The Zenodo concept DOI is intentionally rejected, even when present in
    successful post-release-check output. WAITING output must not be treated
    as DOI metadata readiness.
    """
    if "[WAITING] Zenodo version DOI" in text:
        return None
    escaped = re.escape(version)
    pattern = rf"verified version DOI for v{escaped}: (10\.5281/zenodo\.[0-9]+)"
    match = re.search(pattern, text)
    if not match:
        return None
    doi = match.group(1)
    if doi == CONCEPT_DOI:
        return None
    return doi
