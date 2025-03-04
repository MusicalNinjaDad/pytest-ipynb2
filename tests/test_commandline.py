from pathlib import Path

import pytest

from pytest_ipynb2._pytester_helpers import ExampleDir, ExampleDirSpec


@pytest.mark.parametrize(
    "example_dir",
    [
        ExampleDirSpec(
            files=[Path("tests/assets/notebook_2tests.ipynb").absolute()],
            conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
        ),
    ],
    indirect=True,
)
def test_runnotebook(example_dir: ExampleDir):
    result = example_dir.pytester.runpytest("notebook_2tests.ipynb")
    result.assert_outcomes(passed=3)


@pytest.mark.parametrize(
    "example_dir",
    [
        ExampleDirSpec(
            files=[Path("tests/assets/notebook_2tests.ipynb").absolute()],
        ),
    ],
    indirect=True,
)
def test_cell(example_dir: ExampleDir):
    # Loading in conftest.py is too late to allow for passing Cell-Nodes at commandline(!)
    result = example_dir.pytester.runpytest("-p", "pytest_ipynb2.plugin", "notebook_2tests.ipynb::Cell4")
    result.assert_outcomes(passed=2)
