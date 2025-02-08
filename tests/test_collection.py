from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent

import pytest

from pytest_ipynb2.pytester_helpers import CollectionTree


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


@pytest.fixture
def example_dir2files(example_module: Path, pytester: pytest.Pytester) -> pytest.Pytester:
    """The contents of `notebook.py` as `test_module.py` in an instantiated `Pytester` setup."""
    pytester.makepyfile(test_module=example_module.read_text())
    pytester.makepyfile(test_othermodule=example_module.read_text())
    return pytester


def test_pytestersetup2files(example_dir2files: pytest.Pytester):
    expected_files = ["test_module.py", "test_othermodule.py"]
    files_exist = ((example_dir2files.path / expected_file).exists() for expected_file in expected_files)
    assert all(files_exist), str(list(example_dir2files.path.iterdir()))


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
        items=example_dir.genitems([dir_node]),
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


@pytest.fixture
def expectedtree(example_dir: pytest.Pytester):
    tree = {
        (f"<Dir {example_dir.path.name}>", pytest.Dir): {
            ("<Module test_module.py>", pytest.Module): {
                ("<Function test_adder>", pytest.Function): None,
                ("<Function test_globals>", pytest.Function): None,
            },
        },
    }
    return CollectionTree.from_dict(tree)


def test_expectedtree_repr(expectedtree: CollectionTree, example_dir: pytest.Pytester):
    assert repr(expectedtree) == dedent(f"""\
        <Dir {example_dir.path.name}> (<class '_pytest.main.Dir'>)
            <Module test_module.py> (<class '_pytest.python.Module'>)
                <Function test_adder> (<class '_pytest.python.Function'>)
                <Function test_globals> (<class '_pytest.python.Function'>)
        """)


def test_collectiontree(expectedtree: CollectionTree, collection_nodes: CollectedDir):
    tree = CollectionTree.from_items(collection_nodes.items)
    assert expectedtree == tree
    assert repr(tree) == dedent(f"""\
        <Dir {collection_nodes.pytester_instance.path.name}>
            <Module test_module.py>
                <Function test_adder>
                <Function test_globals>
        """)


@pytest.fixture
def expectedtree_2files(example_dir2files: pytest.Pytester):
    tree = {
        (f"<Dir {example_dir2files.path.name}>", pytest.Dir): {
            ("<Module test_module.py>", pytest.Module): {
                ("<Function test_adder>", pytest.Function): None,
                ("<Function test_globals>", pytest.Function): None,
            },
            ("<Module test_othermodule.py>", pytest.Module): {
                ("<Function test_adder>", pytest.Function): None,
                ("<Function test_globals>", pytest.Function): None,
            },
        },
    }
    return CollectionTree.from_dict(tree)


def test_expectedtree_2files_repr(expectedtree_2files: CollectionTree, example_dir2files: pytest.Pytester):
    assert repr(expectedtree_2files) == dedent(f"""\
        <Dir {example_dir2files.path.name}> (<class '_pytest.main.Dir'>)
            <Module test_module.py> (<class '_pytest.python.Module'>)
                <Function test_adder> (<class '_pytest.python.Function'>)
                <Function test_globals> (<class '_pytest.python.Function'>)
            <Module test_othermodule.py> (<class '_pytest.python.Module'>)
                <Function test_adder> (<class '_pytest.python.Function'>)
                <Function test_globals> (<class '_pytest.python.Function'>)
        """)
