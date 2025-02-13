from pathlib import Path

import pytest
from conftest import CollectedDir


@pytest.mark.parametrize(
    ["example_dir", "expected_files"],
    [
        pytest.param(
            [Path("tests/assets/module.py").absolute()],
            ["test_module.py"],
            id="One File",
        ),
        pytest.param(
            [Path("tests/assets/module.py").absolute(), Path("tests/assets/othermodule.py").absolute()],
            ["test_module.py", "test_othermodule.py"],
            id="Two files",
        ),
    ],
    indirect=["example_dir"],
)
def test_pytestersetup(example_dir: CollectedDir, expected_files: list[str]):
    tmp_path = example_dir.pytester_instance.path
    files_exist = ((tmp_path / expected_file).exists() for expected_file in expected_files)
    assert all(files_exist), f"These are not the files you are looking for: {list(tmp_path.iterdir())}"
