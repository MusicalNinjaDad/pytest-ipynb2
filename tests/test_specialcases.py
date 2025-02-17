"""
Errors which only occur in these tests are likely due to the handling of the specific case, not basic functionality.

TODO:
- parametrized tests
"""  # noqa: D405

from dataclasses import dataclass, field

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

fixture_test = [
    r"%%ipytest",
    "import pytest",
    "@pytest.fixture",
    "def fixt():",
    "    return 1",
    "def test_fixture(fixt):",
    "    assert fixt == 1",
]


@dataclass
class ExpectedResults:
    outcomes: dict[str, int]
    """Dict of outcomes for https://docs.pytest.org/en/stable/reference/reference.html#pytest.RunResult.assert_outcomes"""
    stdout: list[str] = field(default_factory=list)
    """Consecutive lines expected in stdout"""


parametrized = pytest.mark.parametrize(
    ["example_dir", "expected_results"],
    [
        pytest.param(
            ExampleDir(
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
                notebooks={"passing": passing_test},
            ),
            ExpectedResults(
                outcomes={"passed": 1},
            ),
            id="Single Cell",
        ),
        pytest.param(
            ExampleDir(
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
                notebooks={"failing": failing_test},
            ),
            ExpectedResults(
                outcomes={"failed": 1},
                stdout=[
                    "    def test_fails():",
                    "        x = 1",
                    ">       assert x == 2",
                    "E       assert 1 == 2",
                ],
            ),
            id="Failing Test",
        ),
        pytest.param(
            ExampleDir(
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
                notebooks={"fixture": fixture_test},
            ),
            ExpectedResults(
                outcomes={"passed": 1},
            ),
            id="Test with fixture",
        ),
    ],
    indirect=["example_dir"],
)


@parametrized
def test_results(example_dir: CollectedDir, expected_results: ExpectedResults):
    results = example_dir.pytester_instance.runpytest()
    results.assert_outcomes(**expected_results.outcomes)


@parametrized
def test_output(example_dir: CollectedDir, expected_results: ExpectedResults):
    results = example_dir.pytester_instance.runpytest()
    if expected_results.stdout:
        pytest.xfail(reason="meaningful stdout NotImplemented")
        assert results.stdout.fnmatch_lines(expected_results.stdout, consecutive=True)
