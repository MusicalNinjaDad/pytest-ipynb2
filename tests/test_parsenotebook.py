from pathlib import Path
from textwrap import dedent

import pytest

from pytest_ipynb2._parser import CellSource, Notebook


@pytest.fixture
def testnotebook():
    notebook = Path("tests/assets/notebook.ipynb").absolute()
    return Notebook(notebook)


def test_codecells_indexes(testnotebook: Notebook):
    assert list(testnotebook.muggled_codecells.ids()) == [1, 3, 5]


def test_testcells_indexes(testnotebook: Notebook):
    assert list(testnotebook.muggled_testcells.ids()) == [4]


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
    assert testnotebook.muggled_testcells[4] == "\n".join(expected)


def test_codecells_index_a_testcell(testnotebook: Notebook):
    msg = "Cell 4 is not present in this SourceList."
    with pytest.raises(IndexError, match=msg):
        testnotebook.muggled_codecells[4]


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
    assert testnotebook.muggled_testcells == expected


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
    assert testnotebook.muggled_testcells[:] == ["\n".join(expected)]


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
    assert testnotebook.muggled_codecells[:4] == expected


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
            id="ipytest cellmagic at start",
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
            id="line magic call not at start",
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
        pytest.param(
            [
                "result = ipytest.exitcode",
            ],
            [
                "# result = ipytest.exitcode",
            ],
            id="ipytest in expression",
        ),
        pytest.param(
            [
                "ipytest.autoconfig()",
            ],
            [
                "# ipytest.autoconfig()",
            ],
            id="ipytest autoconfig",
        ),
        pytest.param(
            [
                "import ipytest",
            ],
            [
                "# import ipytest",
            ],
            id="import ipytest",
        ),
        pytest.param(
            [
                "import ipytest as ipt",
                "",
                "ipt.autoconfig()",
            ],
            [
                "# import ipytest as ipt",
                "",
                "# ipt.autoconfig()",
            ],
            id="import ipytest as ipt",
        ),
        pytest.param(
            [
                "from ipytest import autoconfig",
                "",
                "autoconfig()",
            ],
            [
                "# from ipytest import autoconfig",
                "",
                "# autoconfig()",
            ],
            id="from ipytest import",
        ),
        pytest.param(
            [
                "from ipytest import autoconfig as aptac",
                "",
                "aptac()",
            ],
            [
                "# from ipytest import autoconfig as aptac",
                "",
                "# aptac()",
            ],
            id="from ipytest import as",
        ),
        pytest.param(
            [
                "from datetime import datetime",
                "",
                "now = datetime.now()",
            ],
            [
                "from datetime import datetime",
                "",
                "now = datetime.now()",
            ],
            id="import from non-magic module",
        ),
    ],
)
def test_muggle(source: list[str], expected: list[str]):
    muggled = CellSource(source).muggled
    assert muggled == CellSource(expected)
