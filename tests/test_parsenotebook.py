from pathlib import Path
from textwrap import dedent

import pytest

from pytest_ipynb2._parser import Notebook


@pytest.fixture
def testnotebook():
    notebook = Path("tests/assets/notebook.ipynb").absolute()
    return Notebook(notebook)


@pytest.fixture
def testnotebook_codecells(testnotebook) -> dict:
    return testnotebook.getcodecells()


@pytest.fixture
def testnotebook_testcells(testnotebook) -> dict:
    return testnotebook.gettestcells()


# TODO(sourcery): #2 Handling of empty notebook
# TODO(sourcery): #3 Test multiple %%ipytest cells in one notebook
# TODO(sourcery): #4 Add tests for cells with only comments, empty cells, and cells with mixed code and markdown.


def test_codecells_number(testnotebook_codecells: dict):
    assert len(testnotebook_codecells) == 3


def test_codecells_indexes(testnotebook_codecells: dict):
    assert list(testnotebook_codecells.keys()) == [1, 3, 5]


def test_testcells_number(testnotebook_testcells: dict):
    assert len(testnotebook_testcells) == 1


def test_testcells_indexes(testnotebook_testcells: dict):
    assert list(testnotebook_testcells.keys()) == [4]


def test_testcell_contents(testnotebook_testcells: dict):
    expected = dedent("""\
        def test_adder():
            assert adder(1, 2) == 3


        def test_globals():
            assert x == 1""")
    assert testnotebook_testcells[4] == expected


def test_cellsourcelists(testnotebook: Notebook):
    codesources = [cellsource for cellsource in testnotebook.codecells if cellsource is not None]
    assert codesources == list(testnotebook.getcodecells().values())

def test_sources_testcells(testnotebook: Notebook):
    expected = [
        None,
        None,
        None,
        None,
        dedent("""\
            def test_adder():
                assert adder(1, 2) == 3


            def test_globals():
                assert x == 1"""),
        None,
    ]
    assert testnotebook.testcells == expected