from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from pytest_ipynb2.pytester_helpers import CollectedDir, ExampleDir

if TYPE_CHECKING:
    from pytest_ipynb2.plugin import Cell


@pytest.mark.parametrize(
    "example_dir",
    [
        pytest.param(
            ExampleDir(
                files=[Path("tests/assets/notebook.ipynb").absolute()],
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
            ),
            id="Simple Notebook",
        ),
    ],
    indirect=True,
)
def test_runtests(example_dir: CollectedDir):
    results = example_dir.pytester_instance.runpytest()
    results.assert_outcomes(passed=2)

@pytest.mark.parametrize(
    "example_dir",
    [
        pytest.param(
            ExampleDir(
                files=[Path("tests/assets/notebook.ipynb").absolute()],
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
            ),
            id="Simple Notebook",
        ),
    ],
    indirect=True,
)
def test_cellmodule_contents(example_dir: CollectedDir):
    cell: Cell = example_dir.items[0].parent
    expected_contents = ["x", "y", "adder", "test_adder", "test_globals"]
    public_items = [attr for attr in cell._obj.__dict__ if not attr.startswith("__")]  # noqa: SLF001
    missing_items = [attr for attr in expected_contents if attr not in public_items]
    assert not missing_items
