from pathlib import Path
from textwrap import dedent

import pytest

from pytest_ipynb2 import getcodecells


@pytest.fixture
def testnotebook():
    notebook = Path("tests/assets/notebook.ipynb").absolute()
    assert notebook.exists()
    return notebook

@pytest.fixture
def testnotebook_codecells(testnotebook: Path) -> dict:
    return getcodecells(testnotebook)

def test_codecells_number(testnotebook_codecells: dict):
    assert len(testnotebook_codecells) == 3

def test_codecells_indexes(testnotebook_codecells: dict):
    assert list(testnotebook_codecells.keys()) == [1,3,4]

def test_codecell4(testnotebook_codecells: dict):
    expected = dedent("""\
        %%ipytest

        def test_adder():
            assert adder(1,2) == 3""")
    assert testnotebook_codecells[4] == expected