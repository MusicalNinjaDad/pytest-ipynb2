from __future__ import annotations

import re
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

import pytest

from pytest_ipynb2._pytester_helpers import CollectionTree, ExampleDirSpec

if TYPE_CHECKING:
    from pytest_ipynb2._pytester_helpers import ExampleDir


@pytest.fixture
def expected_tree(request: pytest.FixtureRequest, example_dir: ExampleDir) -> CollectionTree:
    trees = {
        "test_module": {
            ("<Session  exitstatus='<UNSET>' testsfailed=0 testscollected=0>", pytest.Session): {
                (f"<Dir {example_dir.path.name}>", pytest.Dir): {
                    ("<Module test_module.py>", pytest.Module): {
                        ("<Function test_adder>", pytest.Function): None,
                        ("<Function test_globals>", pytest.Function): None,
                    },
                },
            },
        },
        "two_modules": {
            ("<Session  exitstatus='<UNSET>' testsfailed=0 testscollected=0>", pytest.Session): {
                (f"<Dir {example_dir.path.name}>", pytest.Dir): {
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


def test_from_dict_single_root():
    tree_dict = {
        ("<Function test_adder>", pytest.Function): None,
        ("<Function test_globals>", pytest.Function): None,
    }
    expected_msg = re.escape(f"Please provide a dict with exactly 1 top-level entry (root), not {tree_dict}")
    with pytest.raises(ValueError, match=expected_msg):
        CollectionTree.from_dict(tree_dict)


@pytest.mark.parametrize(
    ["example_dir", "expected_tree"],
    [
        pytest.param(
            ExampleDirSpec(
                files=[Path("tests/assets/test_module.py").absolute()],
            ),
            "test_module",
            id="One module",
        ),
        pytest.param(
            ExampleDirSpec(
                files=[
                    Path("tests/assets/test_module.py").absolute(),
                    Path("tests/assets/test_othermodule.py").absolute(),
                ],
            ),
            "two_modules",
            id="Two modules",
        ),
    ],
    indirect=True,
)
def test_from_items(example_dir: ExampleDir, expected_tree: CollectionTree):
    tree = CollectionTree.from_items(example_dir.items)
    assert tree == expected_tree


def test_no_items():
    expected_msg = "Items list is empty."
    with pytest.raises(ValueError, match=expected_msg):
        CollectionTree.from_items([])
