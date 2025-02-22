from pathlib import Path

import pytest

from pytest_ipynb2._pytester_helpers import CollectedDir, ExampleDir


@pytest.mark.parametrize(
    ["example_dir", "outcomes"],
    [
        pytest.param(
            ExampleDir(
                files=[Path("tests/assets/notebook.ipynb").absolute()],
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
            ),
            {
                "passed": 2,
            },
            id="Simple Notebook",
        ),
        pytest.param(
            ExampleDir(
                files=[Path("tests/assets/notebook_2tests.ipynb").absolute()],
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
            ),
            {
                "passed": 3,
            },
            id="Notebook 2 test cells",
        ),
        pytest.param(
            ExampleDir(
                files=[
                    Path("tests/assets/notebook_2tests.ipynb").absolute(),
                    Path("tests/assets/notebook.ipynb").absolute(),
                ],
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
            ),
            {
                "passed": 5,
            },
            id="Both notebooks - unsorted",
        ),
    ],
    indirect=["example_dir"],
)
def test_runtests(example_dir: CollectedDir, outcomes: dict):
    results = example_dir.pytester_instance.runpytest()
    results.assert_outcomes(**outcomes)



