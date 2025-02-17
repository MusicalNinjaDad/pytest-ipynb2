from pathlib import Path
from textwrap import dedent

import nbformat
import pytest

from pytest_ipynb2.pytester_helpers import CollectedDir, ExampleDir

test_cases = [
    pytest.param(
        ExampleDir(
            [Path("tests/assets/test_module.py").absolute()],
        ),
        {"test_module.py": None},
        id="One File",
    ),
    pytest.param(
        ExampleDir(
            [Path("tests/assets/test_module.py").absolute(), Path("tests/assets/test_othermodule.py").absolute()],
        ),
        {
            "test_module.py": None,
            "test_othermodule.py": None,
        },
        id="Two files",
    ),
    pytest.param(
        ExampleDir(
            [Path("tests/assets/notebook.ipynb").absolute()],
        ),
        {"notebook.ipynb": None},
        id="Simple Notebook",
    ),
    pytest.param(
        ExampleDir(
            notebooks={
                "generated": [
                    "def test_pass():",
                    "    assert True",
                ],
            },
        ),
        {
            "generated.ipynb": [
                dedent("""\
                    def test_pass():
                        assert True"""),
            ],
        },
        id="Generated Notebook",
    ),
]


@pytest.mark.parametrize(
    ["example_dir", "expected_files"],
    test_cases,
    indirect=["example_dir"],
)
def test_filesexist(example_dir: CollectedDir, expected_files: list[str]):
    tmp_path = example_dir.pytester_instance.path
    files_exist = ((tmp_path / expected_file).exists() for expected_file in expected_files)
    assert all(files_exist), f"These are not the files you are looking for: {list(tmp_path.iterdir())}"


@pytest.mark.parametrize(
    ["example_dir", "expected_files"],
    test_cases,
    indirect=["example_dir"],
)
def test_filecontents(example_dir: CollectedDir, expected_files: dict[str, list[str]]):
    tmp_path = example_dir.pytester_instance.path
    for filename, expected_contents in expected_files.items():
        if expected_contents is not None:
            nb = nbformat.read(fp=tmp_path / filename, as_version=nbformat.NO_CONVERT)
            assert [cell.source for cell in nb.cells] == expected_contents
