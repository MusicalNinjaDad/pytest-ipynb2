from pathlib import Path
from textwrap import dedent

import pytest

from pytest_ipynb2._parser import Notebook, SourceList

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
        "\n".join(
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


@pytest.mark.parametrize(
    ["source", "expected"],
    [
        pytest.param(
            [
                r"%%ipytest",
                "",
                "x=2",
            ],
            [
                r"# %%ipytest",
                "",
                "x=2",
            ],
            id="ipytest at start",
        ),
        pytest.param(
            [
                "# initialise matplotlib",
                r"%matplotlib",
                "",
                "x=2",
            ],
            [
                "# initialise matplotlib",
                r"# %matplotlib",
                "",
                "x=2",
            ],
            id="magic call not at start",
        ),
        pytest.param(
            [
                r"env = %env",
            ],
            [
                r"# env = %env",
            ],
            id="magic in expression",
        ),
    ],
)
def test_muggle(source: list[str], expected: list[str]):
    muggled = SourceList(["\n".join(source)]).muggle()
    assert muggled == ["\n".join(expected)]
