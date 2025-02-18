"""Tests failures are likely due to the handling of the specific case, not basic functionality."""

import re
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from pytest_ipynb2.pytester_helpers import CollectedDir, ExampleDir

LINESTART = "^"
LINEEND = "$"
WHITESPACE = r"\s*"


@dataclass
class ExpectedResults:
    outcomes: dict[str, int]
    """Dict of outcomes for https://docs.pytest.org/en/stable/reference/reference.html#pytest.RunResult.assert_outcomes"""
    logreport: list[tuple[str, str, int]] = field(default_factory=list)
    """Contents of logreport for -v execution. Tuple: line-title, short-form results, overall progress (%)"""


parametrized = pytest.mark.parametrize(
    ["example_dir", "expected_results"],
    [
        pytest.param(
            ExampleDir(
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
                notebooks={"passing": [Path("tests/assets/passing_test.py").read_text()]},
            ),
            ExpectedResults(
                outcomes={"passed": 1},
                logreport=[("passing.ipynb:0", ".", 100)],
            ),
            id="Single Cell",
        ),
        pytest.param(
            ExampleDir(
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
                notebooks={"failing": [Path("tests/assets/failing_test.py").read_text()]},
            ),
            ExpectedResults(
                outcomes={"failed": 1},
                # stdout=[
                #     "    def test_fails():",
                #     "        x = 1",
                #     ">       assert x == 2",
                #     "E       assert 1 == 2",
                # ],
            ),
            id="Failing Test",
        ),
        pytest.param(
            ExampleDir(
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
                notebooks={"fixture": [Path("tests/assets/fixture_test.py").read_text()]},
            ),
            ExpectedResults(
                outcomes={"passed": 1},
            ),
            id="Test with fixture",
        ),
        pytest.param(
            ExampleDir(
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
                notebooks={"marks": [Path("tests/assets/param_test.py").read_text()]},
            ),
            ExpectedResults(
                outcomes={"passed": 1, "xfailed": 1},
            ),
            id="Test with parameters and marks",
        ),
        pytest.param(
            ExampleDir(
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
                notebooks={
                    "autoconfig": [
                        Path("tests/assets/import_ipytest.py").read_text(),
                        Path("tests/assets/passing_test.py").read_text(),
                    ],
                },
            ),
            ExpectedResults(
                outcomes={"passed": 1},
            ),
            id="Notebook calls autoconfig",
        ),
        pytest.param(
            ExampleDir(
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
                notebooks={
                    "notests": [Path("tests/assets/test_module.py").read_text()],
                },
            ),
            ExpectedResults(
                outcomes={},
            ),
            id="No ipytest cells",
        ),
        pytest.param(
            ExampleDir(
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
                notebooks={
                    "nocells": [],
                },
            ),
            ExpectedResults(
                outcomes={},
            ),
            id="Empty notebook",
        ),
        pytest.param(
            ExampleDir(
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
                notebooks={
                    "comments": [
                        f"# A test cell\n{Path('tests/assets/passing_test.py').read_text()}",
                        Path("tests/assets/failing_test.py").read_text(),
                    ],
                },
            ),
            ExpectedResults(
                outcomes={"passed": 1, "failed": 1},
            ),
            id="ipytest not first line",
        ),
        pytest.param(
            ExampleDir(
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
                files=[
                    Path("tests/assets/test_module.py"),
                    Path("tests/assets/notebook.ipynb"),
                ],
            ),
            ExpectedResults(
                outcomes={"passed": 4},
            ),
            id="mixed file types",
        ),
        pytest.param(
            ExampleDir(
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
                notebooks={
                    "globals": [
                        "x = 2",
                        "x = 1",
                        Path("tests/assets/globals_test.py").read_text(),
                        "x = 2",
                        Path("tests/assets/globals_test.py").read_text(),
                    ],
                },
            ),
            ExpectedResults(
                outcomes={"passed": 1, "failed": 1},
            ),
            id="cell execution order",
        ),
        pytest.param(
            ExampleDir(
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
                files=[Path("tests/assets/test_module.py")],
            ),
            ExpectedResults(
                outcomes={"passed": 2},
                logreport=[("test_module.py", "..", 100)],
            ),
            id="output python module",
        ),
    ],
    indirect=["example_dir"],
)


@parametrized
def test_results(example_dir: CollectedDir, expected_results: ExpectedResults):
    results = example_dir.pytester_instance.runpytest()
    try:
        results.assert_outcomes(**expected_results.outcomes)
    except AssertionError:
        pytest.fail(f"{results.stdout}")


@parametrized
def test_logreport(example_dir: CollectedDir, expected_results: ExpectedResults):
    results = example_dir.pytester_instance.runpytest()
    if expected_results.logreport:
        stdout_regexes = [
            f"{LINESTART}{re.escape(filename)}{WHITESPACE}"
            f"{re.escape(outcomes)}{WHITESPACE}"
            f"{re.escape('[')}{progress}%{re.escape(']')}{WHITESPACE}{LINEEND}"
            for filename, outcomes, progress in expected_results.logreport
        ]
        results.stdout.re_match_lines(stdout_regexes)
