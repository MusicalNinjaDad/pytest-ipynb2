from pathlib import Path
from textwrap import dedent

import pytest

from pytest_ipynb2._parser import Notebook

# TODO(MusicalNinjaDad): #23 Add tests for multiple lines with `%%ipytest` and calls to ipytest functions


@pytest.fixture
def testnotebook():
    notebook = Path("tests/assets/notebook.ipynb").absolute()
    return Notebook(notebook)


def test_codecells_indexes(testnotebook: Notebook):
    assert list(testnotebook.codecells.ids()) == [1, 3, 5]


def test_testcells_indexes(testnotebook: Notebook):
    assert list(testnotebook.testcells.ids()) == [4]


def test_testcell_contents(testnotebook: Notebook):
    expected = [
        r"# %%ipytest",
        "",
        "",
        "def test_adder():",
        "    assert adder(1, 2) == 3",
        "",
        "",
        "def test_globals():",
        "    assert x == 1",
    ]
    assert testnotebook.testcells[4] == "\n".join(expected)


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
        "\n".join(  # noqa: FLY002
            [
                r"# %%ipytest",
                "",
                "",
                "def test_adder():",
                "    assert adder(1, 2) == 3",
                "",
                "",
                "def test_globals():",
                "    assert x == 1",
            ],
        ),
        None,
    ]
    assert testnotebook.testcells == expected


def test_testcell_fullslice(testnotebook: Notebook):
    expected = [
        r"# %%ipytest",
        "",
        "",
        "def test_adder():",
        "    assert adder(1, 2) == 3",
        "",
        "",
        "def test_globals():",
        "    assert x == 1",
    ]
    assert testnotebook.testcells[:] == ["\n".join(expected)]


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
