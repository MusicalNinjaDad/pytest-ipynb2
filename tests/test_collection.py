from pathlib import Path

import pytest


@pytest.fixture
def example_module() -> Path:
    """
    Location of example file.

    As a fixture: using a constant causes resolution errors due to pytester messing with the path.
    If used directly in a test, fixture MUST be called BEFORE the pytester fixture to avoid path resolution issues.
    """
    return Path("tests/assets/notebook.py").absolute()

@pytest.fixture
def example_dir(example_module: Path, pytester: pytest.Pytester) -> pytest.Pytester:
    """The contents of the code cells in `notebook.ipynb` as `test_module.py` in an instantiated `Pytester` setup."""
    pytester.makepyfile(test_module=example_module.read_text())
    return pytester

def test_pytestersetup(example_dir: pytest.Pytester):
    expected_file = example_dir.path / "test_module.py"
    assert expected_file.exists(), str(list(example_dir.path.iterdir()))

def test_collection(example_dir: pytest.Pytester):
    file_node = example_dir.getpathnode("test_module.py")
    assert type(file_node) is pytest.Module
    testcases = example_dir.genitems([file_node])
    assert len(testcases) == 2
    assert all(type(testcase) is pytest.Function for testcase in testcases)
    assert [testcase.name for testcase in testcases] == ["test_adder", "test_globals"]