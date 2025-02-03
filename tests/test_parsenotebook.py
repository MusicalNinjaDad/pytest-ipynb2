from pathlib import Path
from textwrap import dedent

import pytest

from pytest_ipynb2 import getcodecells, gettestcells


@pytest.fixture
def testnotebook():
    notebook = Path("tests/assets/notebook.ipynb").absolute()
    assert notebook.exists()
    return notebook

@pytest.fixture
def testnotebook_codecells(testnotebook: Path) -> dict:
    return getcodecells(testnotebook)

@pytest.fixture
def testnotebook_testcells(testnotebook: Path) -> dict:
    return gettestcells(testnotebook)

def test_codecells_number(testnotebook_codecells: dict):
    assert len(testnotebook_codecells) == 3

def test_codecells_indexes(testnotebook_codecells: dict):
    assert list(testnotebook_codecells.keys()) == [1,3,5]

def test_testcells_number(testnotebook_testcells: dict):
    assert len(testnotebook_testcells) == 1

def test_testcells_indexes(testnotebook_testcells: dict):
    assert list(testnotebook_testcells.keys()) == [4]


def test_testcell_contents(testnotebook_testcells: dict):
    expected = dedent("""\
        def test_adder():
            assert adder(1,2) == 3""")
    assert testnotebook_testcells[4] == expected