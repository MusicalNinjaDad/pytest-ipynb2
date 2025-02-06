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
    dir_node = example_dir.getpathnode(example_dir.path)
    assert type(dir_node) is pytest.Dir
    collection_items = example_dir.genitems([dir_node])
    assert len(collection_items) == 2
    assert all(type(testcase) is pytest.Function for testcase in collection_items)
    assert all(testcase.parent.name == "test_module.py" for testcase in collection_items)
    assert all(type(testcase.parent) is pytest.Module for testcase in collection_items)
    assert [testcase.name for testcase in collection_items] == ["test_adder", "test_globals"]