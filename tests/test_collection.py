from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
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

@dataclass
class DummyNode:
    name: str
    nodetype: type

    def __eq__(self, other: pytest.Item | pytest.Collector | Self):
        if isinstance(other, self):
            return self.name == other.name and self.nodetype == other.nodetype
        return self.name == repr(other) and self.nodetype is type(other)

class CollectionTree:
    """A (recursible) tree of pytest collection Nodes."""

    def __init__(self,
                 *_,
                 topnode: pytest.Item | pytest.Collector | DummyNode,
                 children: list[CollectionTree] | None,
                ):
        self.children = children
        self.topnode = topnode

    def __eq__(self, other: Self):
        try:
            return self.children == other.children and self.topnode == other.topnode
        except AttributeError:
            return False
        
    def __repr__(self):
        # TODO add a decent repr so it's easier to fix issues with from_dict
        pass

    @classmethod
    def from_dict(cls, contents: dict[tuple[str,type], dict | None | Self]):
        """
        Create a dummy CollectionTree from a dict of dicts with following format:
        
        ```
        { (str: name, type: Nodetype):
            { (str: name, type: Nodetype): (if node is a Collector)
                { , ...
                }
            }
            | None (if node is an Item)
        }
        ```
        """  # noqa: D415
        if len(contents) != 1:
            msg = f"Please provide a dict with exaclty 1 entry, not {contents}"
            raise ValueError(msg)
        for topnodedetails, contentsdict in contents.items():
            for childnode, grandchildren in contentsdict.items():
                if grandchildren is None:
                    return cls(topnode = childnode, children = None)
            return cls(
                topnode = DummyNode(*topnodedetails),
                children=[cls.from_dict({childnode: grandchildren}) ],
            )
        msg = f"Something really wierd happened when creating CollectionTree from: {contents}"
        raise RuntimeError(msg)
        


    @classmethod
    def from_item(cls, item: pytest.Item):
        return cls(topnode=item, children=None)

    @classmethod
    def from_items(cls, items: list[pytest.Item]):
        """Create a CollectionTree from a list of collection items, as returned by `pytester.genitems()`."""
        converteditems = [cls.from_item(item) if not isinstance(item, cls) else item for item in items]
        parents = {item.topnode.parent for item in converteditems}
        items_byparent = {
            parent: [item for item in converteditems if item.topnode.parent == parent]
            for parent in parents
        }
        for parent, children in items_byparent.items():
            if parent.parent is None: # Top of tree
                return cls(topnode=parent, children=children)
            return cls(
                topnode = parent.parent,
                children = [cls(topnode=parent, children=children)],
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

def test_collectiontree(expectedtree: CollectionTree, collection_nodes: CollectedDir):
    tree = CollectionTree.from_items(collection_nodes.items)
    assert expectedtree == tree