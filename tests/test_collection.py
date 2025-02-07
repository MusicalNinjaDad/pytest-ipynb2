from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent, indent
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Self

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

class CollectionTree:
    """
    A (top-down) tree of pytest collection Nodes.
    
    Designed to enable testing the results of collection plugins via:
    ```
    assert CollectionTree.from_items(pytester.genitems([...])) == CollectionTree.from_dict({...})
    ```

    WARNING: Currently only handles a single tree (one top-level node)
    """

    @dataclass
    class _DummyNode:
        """
        A dummy node for a `CollectionTree`, used by `CollectionTree.from_dict()`.

        Compares equal to a genuine `pytest.Node` of the correct type AND where `repr(Node)` == `DummyNode.name`.
        """

        name: str
        nodetype: type
        parent: Self | None = None

        def __eq__(self, other: pytest.Item | pytest.Collector | Self):
            if isinstance(other, type(self)):
                return self.name == other.name and self.nodetype == other.nodetype
            return self.name == repr(other) and self.nodetype is type(other)
        
        def __repr__(self):
            return f"{self.name} ({self.nodetype})"

    def __init__(self,
                 *_,
                 node: pytest.Item | pytest.Collector | _DummyNode,
                 children: list[CollectionTree] | None,
                ):
        """Do not directly initiatise a CollectionTree, use the constructors `from_items()` or `from_dict()` instead."""
        self.children = children
        """
        either:
        - node is `pytest.Collector`: `list[CollectionTree]` of child nodes
        - node is `pytest.Item`: `None`
        """
        self.node = node
        """The actual collected node."""

    def __eq__(self, other: Self):
        """CollectionTrees are equal if their children and node attributes are equal."""
        try:
            return self.children == other.children and self.node == other.node
        except AttributeError:
            return False
        
    def __repr__(self):
        """Indented, multiline representation of the tree to simplify interpreting test failures."""
        if self.children is None:
            children = ""
        else:
            children = indent("\n".join(repr(child).rstrip() for child in self.children), "    ")
        return f"{self.node!r}\n{children}\n"
            

    @classmethod
    def from_dict(cls, tree: dict[tuple[str,type], dict | None]):
        """
        Create a dummy CollectionTree from a dict of dicts with following format:
        
        ```
        {(str: name, type: Nodetype):
            (str: name, type: Nodetype): {
                (str: name, type: Nodetype): None,
                (str: name, type: Nodetype): None
                }
            }
        }
        ```

        For example:
        ```
        tree = {
            (f"<Dir {example_dir.path.name}>", pytest.Dir): {
                ("<Module test_module.py>", pytest.Module): {
                    ("<Function test_adder>", pytest.Function): None,
                    ("<Function test_globals>", pytest.Function): None,
                },
            },
        }
        ```

        """  # noqa: D415
        if len(tree) != 1:
            msg = f"Please provide a dict with exactly 1 entry, not {tree}"
            raise ValueError(msg)
        nodedetails, children = next(iter(tree.items()))
        node = cls._DummyNode(*nodedetails)
        if children is None:
            return cls(node = node, children = None)
        return cls(
            node = node,
            children = [cls.from_dict({childnode: grandchildren}) for childnode, grandchildren in children.items()],
        )

    @classmethod
    def from_item(cls, item: pytest.Item):
        return cls(node=item, children=None)

    @classmethod
    def from_items(cls, items: list[pytest.Item]):
        """Create a CollectionTree from a list of collection items, as returned by `pytester.genitems()`."""
        converteditems = [cls.from_item(item) if not isinstance(item, cls) else item for item in items]
        parents = {item.node.parent for item in converteditems}
        items_byparent = {
            parent: [item for item in converteditems if item.node.parent == parent]
            for parent in parents
        }
        for parent, children in items_byparent.items():
            if parent.parent is None: # Top of tree
                return cls(node=parent, children=children)
            return cls(
                node = parent.parent,
                children = [cls(node=parent, children=children)],
            )
        msg = "Items cannot be empty."
        raise ValueError(msg)


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
