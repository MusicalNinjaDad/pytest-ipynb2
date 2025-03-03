from pathlib import Path

import nbformat
import pytest

from pytest_ipynb2._pytester_helpers import ExampleDir, ExampleDirSpec, add_ipytest_magic

tests = [
    pytest.param(
        ExampleDirSpec(
            files=[Path("tests/assets/test_module.py").absolute()],
        ),
        {"test_module.py": None},
        id="One File",
    ),
    pytest.param(
        ExampleDirSpec(
            files=[Path("tests/assets/test_module.py").absolute(), Path("tests/assets/test_othermodule.py").absolute()],
        ),
        {
            "test_module.py": None,
            "test_othermodule.py": None,
        },
        id="Two files",
    ),
    pytest.param(
        ExampleDirSpec(
            files=[Path("tests/assets/notebook.ipynb").absolute()],
        ),
        {"notebook.ipynb": None},
        id="Copied Notebook",
    ),
    pytest.param(
        ExampleDirSpec(
            notebooks={"generated": [add_ipytest_magic(Path("tests/assets/test_passing.py").read_text())]},
        ),
        {
            "generated.ipynb": [
                add_ipytest_magic(
                    "\n".join(
                        [
                            "def test_pass():",
                            "    assert True",
                        ],
                    ),
                ),
            ],
        },
        id="Generated Notebook",
    ),
    pytest.param(
        ExampleDirSpec(
            notebooks={
                "generated": [
                    Path("tests/assets/import_ipytest.py").read_text(),
                    add_ipytest_magic(Path("tests/assets/test_passing.py").read_text()),
                ],
            },
        ),
        {
            "generated.ipynb": [
                "\n".join(
                    [
                        "import ipytest",
                        "ipytest.autoconfig()",
                        "",
                    ],
                ),
                add_ipytest_magic(
                    "\n".join(
                        [
                            "def test_pass():",
                            "    assert True",
                        ],
                    ),
                ),
            ],
        },
        id="Generated Notebook 2 cells",
    ),
]


@pytest.mark.parametrize(
    ["example_dir", "expected_files"],
    tests,
    indirect=["example_dir"],
)
def test_path(example_dir: ExampleDir, expected_files):  # noqa: ARG001
    assert example_dir.path == example_dir.pytester.path


@pytest.mark.parametrize(
    ["example_dir", "expected_files"],
    tests,
    indirect=["example_dir"],
)
def test_filesexist(example_dir: ExampleDir, expected_files: list[str]):
    tmp_path = example_dir.path
    files_exist = ((tmp_path / expected_file).exists() for expected_file in expected_files)
    assert all(files_exist), f"These are not the files you are looking for: {list(tmp_path.iterdir())}"


@pytest.mark.parametrize(
    ["example_dir", "expected_files"],
    tests,
    indirect=["example_dir"],
)
def test_filecontents(example_dir: ExampleDir, expected_files: dict[str, list[str]]):
    tmp_path = example_dir.path
    for filename, expected_contents in expected_files.items():
        if expected_contents is not None:
            nb = nbformat.read(fp=tmp_path / filename, as_version=nbformat.NO_CONVERT)
            assert [cell.source for cell in nb.cells] == expected_contents


def test_hashable_spec():
    spec = ExampleDirSpec(files=[Path("tests/assets/test_module.py").absolute()])
    assert {spec: None}
