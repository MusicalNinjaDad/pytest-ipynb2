from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent

import pytest

from pytest_ipynb2.pytester_helpers import CollectionTree


@dataclass
class CollectedDir:
    pytester_instance: pytest.Pytester
    dir_node: pytest.Dir
    items: list[pytest.Item]


@pytest.fixture
def example_module() -> Path:
    """
    Location of example file.

    As a fixture: using a constant causes resolution errors due to pytester messing with the path.
    If used directly in a test, fixture MUST be called BEFORE the pytester fixture to avoid path resolution issues.
    """
    return Path("tests/assets/notebook.py").absolute()


@pytest.fixture
def example_dir_old(example_module: Path, pytester: pytest.Pytester) -> pytest.Pytester:
    """The contents of `notebook.py` as `test_module.py` in an instantiated `Pytester` setup."""
    pytester.makepyfile(test_module=example_module.read_text())
    return pytester

@pytest.fixture
def collection_nodes(example_dir_old: pytest.Pytester) -> CollectedDir:
    dir_node = example_dir_old.getpathnode(example_dir_old.path)
    return CollectedDir(
        pytester_instance=example_dir_old,
        dir_node=dir_node,
        items=example_dir_old.genitems([dir_node]),
    )

@pytest.fixture
def example_dir(request: pytest.FixtureRequest, pytester: pytest.Pytester) -> CollectedDir:
    """Parameterised fixture. Requires a list of `Path`s to copy into a pytester instance."""
    files = {f"test_{example.stem}": example.read_text() for example in request.param}
    pytester.makepyfile(**files)
    dir_node = pytester.getpathnode(pytester.path)
    return CollectedDir(
        pytester_instance=pytester,
        dir_node=dir_node,
        items=pytester.genitems([dir_node]),
    )


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


@pytest.fixture
def expected_tree(request: pytest.FixtureRequest, example_dir: CollectedDir) -> CollectionTree:
    trees = {
        "test_module": {
            ("<Session  exitstatus='<UNSET>' testsfailed=0 testscollected=0>", pytest.Session): {
                (f"<Dir {example_dir.pytester_instance.path.name}>", pytest.Dir): {
                    ("<Module test_module.py>", pytest.Module): {
                        ("<Function test_adder>", pytest.Function): None,
                        ("<Function test_globals>", pytest.Function): None,
                    },
                },
            },
        },
    }
    return CollectionTree.from_dict(trees[request.param])


@pytest.mark.parametrize(
    ["example_dir", "expected_tree"],
    [
        pytest.param(
            [Path("tests/assets/module.py").absolute()],
            "test_module",
            id="One File",
        ),
    ],
    indirect=True,
)
def test_from_dict(expected_tree: CollectionTree, example_dir: CollectedDir):
    assert repr(expected_tree) == dedent(f"""\
        <Session  exitstatus='<UNSET>' testsfailed=0 testscollected=0> (<class '_pytest.main.Session'>)
            <Dir {example_dir.pytester_instance.path.name}> (<class '_pytest.main.Dir'>)
                <Module test_module.py> (<class '_pytest.python.Module'>)
                    <Function test_adder> (<class '_pytest.python.Function'>)
                    <Function test_globals> (<class '_pytest.python.Function'>)
        """)

@pytest.mark.parametrize(
    ["example_dir", "expected_tree"],
    [
        pytest.param(
            [Path("tests/assets/module.py").absolute()],
            "test_module",
            id="One File",
        ),
    ],
    indirect=True,
)
def test_from_items(example_dir: CollectedDir, expected_tree: CollectionTree):
    tree = CollectionTree.from_items(example_dir.items)
    assert tree == expected_tree


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


@pytest.fixture
def collection_nodes_2files(example_dir2files: pytest.Pytester) -> CollectedDir:
    dir_node = example_dir2files.getpathnode(example_dir2files.path)
    return CollectedDir(
        pytester_instance=example_dir2files,
        dir_node=dir_node,
        items=example_dir2files.genitems([dir_node]),
    )


@pytest.fixture
def expectedtree_2files(example_dir2files: pytest.Pytester):
    tree = {
        ("<Session  exitstatus='<UNSET>' testsfailed=0 testscollected=0>", pytest.Session): {
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
        },
    }
    return CollectionTree.from_dict(tree)


def test_expectedtree_2files_repr(expectedtree_2files: CollectionTree, example_dir2files: pytest.Pytester):
    assert repr(expectedtree_2files) == dedent(f"""\
        <Session  exitstatus='<UNSET>' testsfailed=0 testscollected=0> (<class '_pytest.main.Session'>)
            <Dir {example_dir2files.path.name}> (<class '_pytest.main.Dir'>)
                <Module test_module.py> (<class '_pytest.python.Module'>)
                    <Function test_adder> (<class '_pytest.python.Function'>)
                    <Function test_globals> (<class '_pytest.python.Function'>)
                <Module test_othermodule.py> (<class '_pytest.python.Module'>)
                    <Function test_adder> (<class '_pytest.python.Function'>)
                    <Function test_globals> (<class '_pytest.python.Function'>)
        """)


def test_collectiontree_2files(expectedtree_2files: CollectionTree, collection_nodes_2files: CollectedDir):
    tree = CollectionTree.from_items(collection_nodes_2files.items)
    assert expectedtree_2files == tree
