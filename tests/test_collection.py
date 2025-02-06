from dataclasses import dataclass
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
    """The contents of `notebook.py` as `test_module.py` in an instantiated `Pytester` setup."""
    pytester.makepyfile(test_module=example_module.read_text())
    return pytester

def test_pytestersetup(example_dir: pytest.Pytester):
    expected_file = example_dir.path / "test_module.py"
    assert expected_file.exists(), str(list(example_dir.path.iterdir()))

@dataclass
class CollectedDir:
    pytester_instance: pytest.Pytester
    dir_node: pytest.Dir
    items: list[pytest.Item]

@pytest.fixture
def collection_nodes(example_dir: pytest.Pytester) -> CollectedDir:
    dir_node = example_dir.getpathnode(example_dir.path)
    return CollectedDir(
        pytester_instance=example_dir,
        dir_node=dir_node,
        items = example_dir.genitems([dir_node]),
    )

def test_collectedDir_type(collection_nodes: CollectedDir):
    assert type(collection_nodes.dir_node) is pytest.Dir
    
def test_collectedItems_count(collection_nodes: CollectedDir):
    assert len(collection_nodes.items) == 2

def test_collectedItems_types(collection_nodes: CollectedDir):
    assert all(type(testcase) is pytest.Function for testcase in collection_nodes.items)

def test_collectedItems_names(collection_nodes: CollectedDir):
    assert [testcase.name for testcase in collection_nodes.items] == ["test_adder", "test_globals"]

def test_collectedItems_parents(collection_nodes: CollectedDir):
    assert all(testcase.parent.name == "test_module.py" for testcase in collection_nodes.items)
    assert all(type(testcase.parent) is pytest.Module for testcase in collection_nodes.items)

def test_collection_depth(collection_nodes: CollectedDir):
    assert all(testcase.parent.parent is collection_nodes.dir_node for testcase in collection_nodes.items)