from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from pytest_ipynb2._pytester_helpers import ExampleDir, ExampleDirSpec, add_ipytest_magic

LINESTART = "^"
LINEEND = "$"
WHITESPACE = r"\s*"


@dataclass
class FailureDetails:
    testcase: str
    filename: str
    details: list[str]
    location: str
    exceptiontype: type[Exception]


@dataclass
class ExpectedResults:
    outcomes: dict[str, int]
    """Dict of outcomes for https://docs.pytest.org/en/stable/reference/reference.html#pytest.RunResult.assert_outcomes"""
    logreport: list[tuple[str, str, int]] = field(default_factory=list)
    """Contents of logreport for -v execution. Tuple: line-title, short-form results, overall progress (%)"""
    summary: list[tuple[str, str, type[Exception] | None, str | None]] | None = field(default_factory=list)
    """
    FULL Contents of test summary info.
    
    - Tuple per line: Result, location, Exception raised, Exception message
    - Explicity pass `None` to express "No test summary" or "Element not included"
    """
    failures: list[FailureDetails] | None = field(default_factory=list)
    """Details of any test failures. Explicity pass `None` to assert no failures."""


parametrized = pytest.mark.parametrize(
    ["example_dir", "expected_results"],
    [
        pytest.param(
            ExampleDirSpec(
                files=[Path("tests/assets/notebook.ipynb").absolute()],
            ),
            ExpectedResults(
                outcomes={"passed": 2},
            ),
            id="Copied notebook",
        ),
        pytest.param(
            ExampleDirSpec(
                files=[Path("tests/assets/notebook_2tests.ipynb").absolute()],
            ),
            ExpectedResults(
                outcomes={"passed": 3},
            ),
            id="Copied notebook with 2 test cells",
        ),
        pytest.param(
            ExampleDirSpec(
                files=[
                    Path("tests/assets/notebook_2tests.ipynb").absolute(),
                    Path("tests/assets/notebook.ipynb").absolute(),
                ],
            ),
            ExpectedResults(
                outcomes={"passed": 5},
            ),
            id="Two copied notebooks - unsorted",
        ),
        pytest.param(
            ExampleDirSpec(
                notebooks={"passing": [add_ipytest_magic(Path("tests/assets/test_passing.py").read_text())]},
            ),
            ExpectedResults(
                outcomes={"passed": 1},
                logreport=[("passing.ipynb[Cell0]", ".", 100)],
                summary=None,
                failures=None,
            ),
            id="Single Cell",
        ),
        pytest.param(
            ExampleDirSpec(
                notebooks={"failing": [add_ipytest_magic(Path("tests/assets/test_failing.py").read_text())]},
            ),
            ExpectedResults(
                outcomes={"failed": 1},
                logreport=[("failing.ipynb[Cell0]", "F", 100)],
                summary=[("FAILED", "failing.ipynb[Cell0]::test_fails", None, "assert 1 == 2")],
                failures=[
                    FailureDetails(
                        testcase="Cell0::test_fails",
                        details=[
                            "    def test_fails():",
                            "        x = 1",
                            ">       assert x == 2",
                            "E       assert 1 == 2",
                        ],
                        filename="failing.ipynb[Cell0]",
                        exceptiontype=AssertionError,
                        location="5",
                    ),
                ],
            ),
            id="Failing Test",
        ),
        pytest.param(
            ExampleDirSpec(
                notebooks={"fixture": [add_ipytest_magic(Path("tests/assets/test_fixture.py").read_text())]},
            ),
            ExpectedResults(
                outcomes={"passed": 1},
            ),
            id="Test with fixture",
        ),
        pytest.param(
            ExampleDirSpec(
                notebooks={"marks": [add_ipytest_magic(Path("tests/assets/test_param.py").read_text())]},
                ini="addopts = -rx",
            ),
            ExpectedResults(
                outcomes={"passed": 1, "xfailed": 1},
                logreport=[("marks.ipynb[Cell0]", ".x", 100)],
                summary=[("XFAIL", "marks.ipynb[Cell0]::test_params[fail]", None, "xfailed")],
            ),
            id="Test with parameters and marks",
        ),
        pytest.param(
            ExampleDirSpec(
                notebooks={
                    "autoconfig": [
                        add_ipytest_magic(Path("tests/assets/import_ipytest.py").read_text()),
                        add_ipytest_magic(Path("tests/assets/test_passing.py").read_text()),
                    ],
                },
            ),
            ExpectedResults(
                outcomes={"passed": 1},
                logreport=[("autoconfig.ipynb[Cell1]", ".", 100)],
            ),
            id="Notebook calls autoconfig",
        ),
        pytest.param(
            ExampleDirSpec(
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
            ExampleDirSpec(
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
            ExampleDirSpec(
                notebooks={
                    "comments": [
                        f"# A test cell\n{add_ipytest_magic(Path('tests/assets/test_passing.py').read_text())}",
                        add_ipytest_magic(Path("tests/assets/test_failing.py").read_text()),
                    ],
                },
            ),
            ExpectedResults(
                outcomes={"passed": 1, "failed": 1},
            ),
            id="ipytest not first line",
        ),
        pytest.param(
            ExampleDirSpec(
                files=[
                    Path("tests/assets/test_module.py"),
                    Path("tests/assets/notebook.ipynb"),
                ],
            ),
            ExpectedResults(
                outcomes={"passed": 4},
                logreport=[("notebook.ipynb[Cell4]", "..", 50), ("test_module.py", "..", 100)],
            ),
            id="mixed file types",
        ),
        pytest.param(
            ExampleDirSpec(
                notebooks={
                    "globals": [
                        "x = 2",
                        "x = 1",
                        add_ipytest_magic(Path("tests/assets/test_globals.py").read_text()),
                        "x = 2",
                        add_ipytest_magic(Path("tests/assets/test_globals.py").read_text()),
                    ],
                },
            ),
            ExpectedResults(
                outcomes={"passed": 1, "failed": 1},
                logreport=[
                    ("globals.ipynb[Cell2]", ".", 50),
                    ("globals.ipynb[Cell4]", "F", 100),
                ],
            ),
            id="cell execution order",
        ),
        pytest.param(
            ExampleDirSpec(
                files=[Path("tests/assets/test_module.py")],
            ),
            ExpectedResults(
                outcomes={"passed": 2},
                logreport=[("test_module.py", "..", 100)],
            ),
            id="output python module",
        ),
        pytest.param(
            ExampleDirSpec(
                ini="addopts = -vv",
                notebooks={
                    "two_cells": [
                        add_ipytest_magic(
                            "\n".join(
                                [
                                    Path("tests/assets/test_passing.py").read_text(),
                                    Path("tests/assets/test_failing.py").read_text(),
                                ],
                            ),
                        ),
                        add_ipytest_magic(Path("tests/assets/test_passing.py").read_text()),
                    ],
                },
            ),
            ExpectedResults(
                outcomes={"passed": 2, "failed": 1},
                logreport=[
                    ("two_cells.ipynb[Cell0]::test_pass", "PASSED", 33),
                    ("two_cells.ipynb[Cell0]::test_fails", "FAILED", 66),
                    ("two_cells.ipynb[Cell1]::test_pass", "PASSED", 100),
                ],
                summary=[("FAILED", "two_cells.ipynb[Cell0]::test_fails", None, "assert 1 == 2")],
            ),
            id="Verbose two notebooks",
        ),
        pytest.param(
            ExampleDirSpec(
                files=[Path("tests/assets/test_failing.py")],
            ),
            ExpectedResults(
                outcomes={"failed": 1},
                logreport=[("test_failing.py", "F", 100)],
                summary=[("FAILED", "test_failing.py::test_fails", None, "assert 1 == 2")],
                failures=[
                    FailureDetails(
                        testcase="test_fails",
                        details=[
                            "    def test_fails():",
                            "        x = 1",
                            ">       assert x == 2",
                            "E       assert 1 == 2",
                        ],
                        filename="test_failing.py",
                        exceptiontype=AssertionError,
                        location="3",
                    ),
                ],
            ),
            id="failing python module",
        ),
        pytest.param(
            ExampleDirSpec(
                path=Path("notebooks"),
                ini="addopts = -vv",
                notebooks={
                    "two_cells": [
                        add_ipytest_magic(
                            "\n".join(
                                [
                                    Path("tests/assets/test_passing.py").read_text(),
                                    Path("tests/assets/test_failing.py").read_text(),
                                ],
                            ),
                        ),
                        add_ipytest_magic(Path("tests/assets/test_passing.py").read_text()),
                    ],
                },
            ),
            ExpectedResults(
                outcomes={"passed": 2, "failed": 1},
                logreport=[
                    ("notebooks/two_cells.ipynb[Cell0]::test_pass", "PASSED", 33),
                    ("notebooks/two_cells.ipynb[Cell0]::test_fails", "FAILED", 66),
                    ("notebooks/two_cells.ipynb[Cell1]::test_pass", "PASSED", 100),
                ],
                summary=[("FAILED", "notebooks/two_cells.ipynb[Cell0]::test_fails", None, "assert 1 == 2")],
            ),
            id="Subdirectory verbose",
        ),
    ],
    indirect=["example_dir"],
)


@parametrized
@pytest.mark.autoskip
def test_outcomes(example_dir: ExampleDir, expected_results: ExpectedResults):
    try:
        example_dir.runresult.assert_outcomes(**expected_results.outcomes)
    except AssertionError:
        pytest.fail(f"{example_dir.runresult.stdout}")


@parametrized
@pytest.mark.autoskip
def test_logreport(example_dir: ExampleDir, expected_results: ExpectedResults):
    stdout_regexes = [
        f"{LINESTART}{re.escape(filename)}{WHITESPACE}"
        f"{re.escape(outcomes)}{WHITESPACE}"
        f"{re.escape('[')}{progress:3d}%{re.escape(']')}{WHITESPACE}{LINEEND}"
        for filename, outcomes, progress in expected_results.logreport
    ]
    example_dir.runresult.stdout.re_match_lines(stdout_regexes, consecutive=True)


@parametrized
@pytest.mark.autoskip
def test_summary(example_dir: ExampleDir, expected_results: ExpectedResults):
    summary_regexes = ["[=]* short test summary info [=]*"]
    if expected_results.summary is not None:
        summary_regexes += [
            f"{re.escape(result)}"
            f"{WHITESPACE}{re.escape(location)}"
            f"{WHITESPACE}{re.escape('-')}{WHITESPACE}"
            f"{'' if exceptiontype is None else re.escape(exceptiontype.__name__)}"
            f"{'' if message is None else re.escape(message)}"
            f"{WHITESPACE}{LINEEND}"
            for result, location, exceptiontype, message in expected_results.summary
        ]  # message is currently not provided until we fix Assertion re-writing
        summary_regexes += ["[=]*"]
        example_dir.runresult.stdout.re_match_lines(summary_regexes, consecutive=True)
    else:
        assert (
            re.search(
                f"{LINESTART}{summary_regexes[0]}{LINEEND}",
                str(example_dir.runresult.stdout),
                flags=re.MULTILINE,
            )
            is None
        )


@parametrized
@pytest.mark.autoskip
def test_failures(example_dir: ExampleDir, expected_results: ExpectedResults):
    results = example_dir.runresult
    regexes = ["[=]* FAILURES [=]*"]
    if expected_results.failures is not None:
        for failure in expected_results.failures:
            regexes += [
                f"[_]* {failure.testcase} [_*]",
                "",
                *failure.details,
                "",
                f"{failure.filename}:{failure.location}: {failure.exceptiontype.__name__}",
            ]
        results.stdout.re_match_lines(regexes, consecutive=True)
    else:
        assert re.search(f"{LINESTART}{regexes[0]}{LINEEND}", str(results.stdout), flags=re.MULTILINE) is None
