from pathlib import Path

import pytest

from pytest_ipynb2._pytester_helpers import ExampleDir, ExampleDirSpec


@pytest.mark.parametrize(
    "example_dir",
    [
        ExampleDirSpec(
            files=[Path("tests/assets/notebook_2tests.ipynb").absolute()],
            args=["notebook_2tests.ipynb"],
        ),
    ],
    indirect=True,
)
def test_runnotebook(example_dir: ExampleDir):
    result = example_dir.runresult
    result.assert_outcomes(passed=3)


@pytest.mark.parametrize(
    "example_dir",
    [
        ExampleDirSpec(
            files=[Path("tests/assets/notebook_2tests.ipynb").absolute()],
            args=["notebook_2tests.ipynb[Cell4]"],
        ),
    ],
    indirect=True,
)
def test_cell(example_dir: ExampleDir):
    result = example_dir.runresult
    result.assert_outcomes(passed=2)


@pytest.mark.parametrize(
    "example_dir",
    [
        ExampleDirSpec(
            files=[Path("tests/assets/notebook_2tests.ipynb").absolute()],
            args=["notebook_2tests.ipynb[Cell4]::test_adder"],
        ),
    ],
    indirect=True,
)
def test_func(example_dir: ExampleDir):
    result = example_dir.runresult
    result.assert_outcomes(passed=1)
