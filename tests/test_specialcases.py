"""
Errors which only occur in these tests are likely due to the handling of the specific case, not basic functionality.

TODO:
- failing tests - Including Assertion rewriting
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
    "   assert False",
]

test_cases = [
    pytest.param(
        ExampleDir(
            conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
            notebooks={"passing": passing_test},
        ),
        {"passed": 1},
        id="Single Cell",
    ),
    pytest.param(
        ExampleDir(
            conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
            notebooks={"failing": failing_test},
        ),
        {"failed": 1},
        id="Failing Test",
    ),
]

@pytest.mark.parametrize(
    ["example_dir", "outcomes"],
    test_cases,
    indirect=["example_dir"],
)
def test_complex_tests(example_dir: CollectedDir, outcomes: dict):
    results = example_dir.pytester_instance.runpytest()
    results.assert_outcomes(**outcomes)