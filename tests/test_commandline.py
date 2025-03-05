from pathlib import Path

import pytest

from pytest_ipynb2._pytester_helpers import ExampleDir, ExampleDirSpec


@pytest.mark.parametrize(
    "example_dir",
    [
        ExampleDirSpec(
            files=[Path("tests/assets/notebook_2tests.ipynb").absolute()],
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
    # TODO: #49 (can't rerun runpytest)
    result = example_dir.pytester.runpytest("<notebook_2tests.ipynb[Cell4]>")
    result.assert_outcomes(passed=2)

@pytest.mark.parametrize(
    "example_dir",
    [
        ExampleDirSpec(
            files=[Path("tests/assets/test_module.py").absolute()],
        ),
    ],
    indirect=True,
)
def test_module(example_dir: ExampleDir):
    result = example_dir.pytester.runpytest("test_module.py")
    result.assert_outcomes(passed=2)


@pytest.mark.parametrize(
    "example_dir",
    [
        ExampleDirSpec(
            files=[Path("tests/assets/test_module.py").absolute()],
        ),
    ],
    indirect=True,
)
def test_func(example_dir: ExampleDir):
    # TODO: #49 (can't rerun runpytest)
    result = example_dir.pytester.runpytest("test_module.py::test_globals")
    result.assert_outcomes(passed=1)
