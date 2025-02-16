from pathlib import Path
from textwrap import dedent

import pytest

from pytest_ipynb2._parser import Notebook


@pytest.fixture
def testnotebook():
    notebook = Path("tests/assets/notebook.ipynb").absolute()
    return Notebook(notebook)


@pytest.fixture
def testnotebook_codecells(testnotebook: Notebook) -> dict:
    return testnotebook.getcodecells()


@pytest.fixture
def testnotebook_testcells(testnotebook: Notebook) -> dict:
    return testnotebook.gettestcells()


# TODO(sourcery): #2 Handling of empty notebook
# TODO(sourcery): #3 Test multiple %%ipytest cells in one notebook
# TODO(sourcery): #4 Add tests for cells with only comments, empty cells, and cells with mixed code and markdown.


def test_codecells_number(testnotebook: Notebook):
    assert len(testnotebook.codecells) == 3


def test_testcells_number(testnotebook: Notebook):
    assert len(testnotebook.testcells) == 1


def test_testcell_contents(testnotebook: Notebook):
    expected = dedent("""\
        def test_adder():
            assert adder(1, 2) == 3


        def test_globals():
            assert x == 1""")
    assert testnotebook.testcells[4] == expected


def test_codecells_index_a_testcell(testnotebook: Notebook):
    msg = "Cell 4 is not present in this SourceList."
    with pytest.raises(IndexError, match=msg):
        testnotebook.codecells[4]


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


def test_testcell_fullslice(testnotebook: Notebook):
    expected = dedent("""\
        def test_adder():
            assert adder(1, 2) == 3


        def test_globals():
            assert x == 1""")
    assert testnotebook.testcells[:] == [expected]


def test_codecells_partial_slice(testnotebook: Notebook):
    expected = [
        dedent("""\
            # This cell sets some global variables

            x = 1
            y = 2

            x + y"""),
        dedent("""\
            # Define a function


            def adder(a, b):
                return a + b"""),
    ]
    assert testnotebook.codecells[:4] == expected

def test_testcells_items(testnotebook: Notebook):
    expected_source = dedent("""\
        def test_adder():
            assert adder(1, 2) == 3


        def test_globals():
            assert x == 1""")
    assert list(testnotebook.testcells.items()) == [(4, expected_source)]