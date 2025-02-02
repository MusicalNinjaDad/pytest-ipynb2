from pathlib import Path

import pytest

from pytest_ipynb2 import getcodecells


@pytest.fixture
def testnotebook():
    notebook = Path("tests/assets/notebook.ipynb").absolute()
    assert notebook.exists()
    return notebook

def test_codecells(testnotebook):
    codecells = getcodecells(testnotebook)
    assert len(codecells) == 3