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


def test_repr():
    tree_dict = {
        ("<Session  exitstatus='<UNSET>' testsfailed=0 testscollected=0>", pytest.Session): {
            ("<Dir tests>", pytest.Dir): {
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
    tree = CollectionTree.from_dict(tree_dict)
    assert repr(tree) == dedent("""\
        <Session  exitstatus='<UNSET>' testsfailed=0 testscollected=0> (<class '_pytest.main.Session'>)
            <Dir tests> (<class '_pytest.main.Dir'>)
                <Module test_module.py> (<class '_pytest.python.Module'>)
                    <Function test_adder> (<class '_pytest.python.Function'>)
                    <Function test_globals> (<class '_pytest.python.Function'>)
                <Module test_othermodule.py> (<class '_pytest.python.Module'>)
                    <Function test_adder> (<class '_pytest.python.Function'>)
                    <Function test_globals> (<class '_pytest.python.Function'>)
        """)


def test_eq():
    tree_dict = {
        ("<Session  exitstatus='<UNSET>' testsfailed=0 testscollected=0>", pytest.Session): {
            ("<Dir tests>", pytest.Dir): {
                ("<Module test_module.py>", pytest.Module): {
                    ("<Function test_adder>", pytest.Function): None,
                    ("<Function test_globals>", pytest.Function): None,
                },
            },
        },
    }
    tree1 = CollectionTree.from_dict(tree_dict)
    tree2 = CollectionTree.from_dict(tree_dict)
    assert tree1 is not tree2
    assert tree1 == tree2
    assert tree1 != tree_dict
    assert tree_dict != tree1


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
        "two_modules": {
            ("<Session  exitstatus='<UNSET>' testsfailed=0 testscollected=0>", pytest.Session): {
                (f"<Dir {example_dir.pytester_instance.path.name}>", pytest.Dir): {
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
        },
    }
    return CollectionTree.from_dict(trees[request.param])


@pytest.mark.parametrize(
    ["example_dir", "expected_tree"],
    [
        pytest.param(
            [Path("tests/assets/module.py").absolute()],
            "test_module",
            id="One module",
        ),
        pytest.param(
            [Path("tests/assets/module.py").absolute(), Path("tests/assets/othermodule.py").absolute()],
            "two_modules",
            id="Two modules",
        ),
    ],
    indirect=True,
)
def test_from_items(example_dir: CollectedDir, expected_tree: CollectionTree):
    tree = CollectionTree.from_items(example_dir.items)
    assert tree == expected_tree
