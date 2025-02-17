from pathlib import Path

import pytest

from pytest_ipynb2.pytester_helpers import CollectedDir, ExampleDir


@pytest.mark.parametrize(
    ["example_dir", "expected_files"],
    [
        pytest.param(
            ExampleDir(
                [Path("tests/assets/test_module.py").absolute()],
            ),
            ["test_module.py"],
            id="One File",
        ),
        pytest.param(
            ExampleDir(
                [Path("tests/assets/test_module.py").absolute(), Path("tests/assets/test_othermodule.py").absolute()],
            ),
            ["test_module.py", "test_othermodule.py"],
            id="Two files",
        ),
        pytest.param(
            ExampleDir(
                [Path("tests/assets/notebook.ipynb").absolute()],
            ),
            ["notebook.ipynb"],
            id="Simple Notebook",
        ),
        pytest.param(
            ExampleDir(
                notebooks = {
                    "generated": [
                        "def test_pass():",
                        "    assert True",
                    ],
                },
            ),
            ["generated.ipynb"],
            id="Generated Notebook",
        ),
    ],
    indirect=["example_dir"],
)
def test_filesexist(example_dir: CollectedDir, expected_files: list[str]):
    tmp_path = example_dir.pytester_instance.path
    files_exist = ((tmp_path / expected_file).exists() for expected_file in expected_files)
    assert all(files_exist), f"These are not the files you are looking for: {list(tmp_path.iterdir())}"
