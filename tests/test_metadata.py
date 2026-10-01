"""Checks that need no release directory, so they run everywhere (CI, a
fresh clone, a wheel install)."""
from importlib.metadata import version

import likingInitiative


def test_package_version_matches_distribution_metadata():
    assert likingInitiative.__version__ == version("likingInitiative")


def test_database_citation_names_the_paper_and_the_data_doi():
    assert "psyarxiv/af2nr_v1" in likingInitiative.cite()
    assert "10.5281/zenodo.22216442" in likingInitiative.cite()
