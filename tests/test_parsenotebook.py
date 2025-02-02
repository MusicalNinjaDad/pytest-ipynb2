from pathlib import Path

import pytest

from pytest_ipynb2 import getcodecells


@pytest.fixture
def testnotebook():
    notebook = Path("tests/assets/notebook.ipynb").absolute()
    assert notebook.exists()
    return notebook

@pytest.fixture
def testnotebook_codecells(testnotebook):
    return getcodecells(testnotebook)

def test_codecells(testnotebook_codecells):
    assert len(testnotebook_codecells) == 3