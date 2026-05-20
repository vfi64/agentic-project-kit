from agentic_project_kit.release_doi_safety import extract_verified_version_doi


def test_waiting_output_does_not_return_concept_doi() -> None:
    output = """Post-release check for target v0.3.33
[PASS] GitHub release: GitHub release exists: v0.3.33
[PASS] Zenodo concept DOI: found DOI: 10.5281/zenodo.20101359
[WAITING] Zenodo version DOI: no verified Zenodo record found yet for v0.3.33; leave README/CITATION unchanged
Overall: PASS
"""
    assert extract_verified_version_doi(output, "0.3.33") is None


def test_concept_doi_alone_is_never_version_doi() -> None:
    output = "Zenodo concept DOI: found DOI: 10.5281/zenodo.20101359"
    assert extract_verified_version_doi(output, "0.3.33") is None


def test_verified_version_specific_doi_is_extracted() -> None:
    output = "Zenodo version DOI: verified version DOI for v0.3.33: 10.5281/zenodo.20399999"
    assert extract_verified_version_doi(output, "0.3.33") == "10.5281/zenodo.20399999"


def test_wrong_version_doi_is_not_extracted() -> None:
    output = "Zenodo version DOI: verified version DOI for v0.3.32: 10.5281/zenodo.20314341"
    assert extract_verified_version_doi(output, "0.3.33") is None
