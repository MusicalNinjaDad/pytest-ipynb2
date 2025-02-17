"""
Errors which only occur in these tests are likely due to the handling of the specific case, not basic functionality.

TODO:
- Assertion rewriting
- tests using fixtures
- parametrized tests
"""  # noqa: D405

import pytest

from pytest_ipynb2.pytester_helpers import CollectedDir, ExampleDir

passing_test = [
    r"%%ipytest",
    "def test_passes():",
    "   assert True",
]

failing_test = [
    r"%%ipytest",
    "def test_fails():",
    "    x = 1",
    "    assert x == 2",
]

test_cases = [
    pytest.param(
        ExampleDir(
            conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
            notebooks={"passing": passing_test},
        ),
        {"passed": 1},
        None,
        id="Single Cell",
    ),
    pytest.param(
        ExampleDir(
            conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
            notebooks={"failing": failing_test},
        ),
        {"failed": 1},
        [
            "    def test_fails():",
            "        x = 1",
            ">       assert x == 2",
            "E       assert 1 == 2",
        ],
        id="Failing Test",
    ),
]


@pytest.mark.parametrize(
    ["example_dir", "outcomes", "stdout"],
    test_cases,
    indirect=["example_dir"],
)
def test_results(example_dir: CollectedDir, outcomes: dict, stdout: list[str]):  # noqa: ARG001
    results = example_dir.pytester_instance.runpytest()
    results.assert_outcomes(**outcomes)


@pytest.mark.parametrize(
    ["example_dir", "outcomes", "stdout"],
    test_cases,
    indirect=["example_dir"],
)
def test_output(example_dir: CollectedDir, outcomes: dict, stdout: list[str]):  # noqa: ARG001
    results = example_dir.pytester_instance.runpytest()
    if stdout:
        pytest.xfail(reason="meaningful stdout NotImplemented")
        assert results.stdout.fnmatch_lines(stdout, consecutive=True)
