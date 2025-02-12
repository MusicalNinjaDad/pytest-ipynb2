"""Helper classes and functions to support testing this plugin with pytester."""

from __future__ import annotations

from dataclasses import dataclass
from textwrap import indent
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from contextlib import suppress

    with suppress(ImportError): # not type-checking on python < 3.11
        from typing import Self

class CollectionTree:
    """
    A (top-down) tree of pytest collection Nodes.

    Designed to enable testing the results of collection plugins via:
    ```
    assert CollectionTree.from_items(pytester.genitems([...])) == CollectionTree.from_dict({...})
    ```

    WARNING: Currently only handles a single tree (one top-level node)
    """

    @classmethod
    def from_items(cls, items: list[pytest.Item]) -> Self:
        """Create a CollectionTree from a list of collection items, as returned by `pytester.genitems()`."""
        def _from_item(item: pytest.Item | Self) -> Self:
            return cls(node=item, children=None) if not isinstance(item, cls) else item
        
        items = [_from_item(item) for item in items]

        def _get_parents_as_CollectionTrees(items: list[Self]) -> list[Self]:  # noqa: N802
            """
            Walk up the tree one step. (Not recursive, does provide sentinel or repeat).
            
            Returns a set of CollectionTree items for the parents of those provided.
            """
            parents = (item.node.parent for item in items)
            items_byparent = {
                parent: [item for item in items if item.node.parent == parent]
                for parent in parents
            }
            return [
                cls(node = parent, children = list(children))
                for parent, children in items_byparent.items()
            ]
        
        if all(isinstance(item.node, pytest.Session) for item in items):
            return next(iter(items)) # Should only be one session

        return cls.from_items(_get_parents_as_CollectionTrees(items))

    @classmethod
    def from_dict(cls, tree: dict[tuple[str, type], dict | None]) -> Self:
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
            (f"<Dir {pytester.path.name}>", pytest.Dir): {
                ("<Module test_module.py>", pytest.Module): {
                    ("<Function test_adder>", pytest.Function): None,
                    ("<Function test_globals>", pytest.Function): None,
                },
            },
        }
        ```
        """  # noqa: D415
        if len(tree) != 1:
            msg = f"Please provide a dict with exactly 1 top-level entry (root), not {tree}"
            raise ValueError(msg)
        nodedetails, children = next(iter(tree.items()))
        node = cls._DummyNode(*nodedetails)

        if children is not None:
            return cls(
                node=node,
                children=[
                    cls.from_dict({childnode: grandchildren})
                    for childnode, grandchildren in children.items()
                ],
            )

        return cls(node=node, children=None)

    @dataclass
    class _DummyNode:
        """
        A dummy node for a `CollectionTree`, used by `CollectionTree.from_dict()`.

        Compares equal to a genuine `pytest.Node` of the correct type AND where `repr(Node)` == `DummyNode.name`.
        """

        name: str
        nodetype: type
        parent: Self | None = None
        """Currently always None but required to avoid attribute errors if type checking Union[pytest.Node,_DummNode]"""

        def __eq__(self, other: pytest.Item | pytest.Collector | Self) -> bool:
            if isinstance(other, type(self)):
                return self.name == other.name and self.nodetype == other.nodetype
            return self.name == repr(other) and self.nodetype is type(other)

        def __repr__(self) -> str:
            return f"{self.name} ({self.nodetype})"

    def __init__(
        self,
        *_,  # noqa: ANN002
        node: pytest.Item | pytest.Collector | _DummyNode,
        children: list[CollectionTree] | None,
    ):
        """Do not directly initiatise a CollectionTree, use the constructors `from_items()` or `from_dict()` instead."""
        self.children = children
        """
        either:
        - if node is `pytest.Collector`: a `list[CollectionTree]` of child nodes
        - if node is `pytest.Item`: `None`
        """
        self.node = node
        """The actual collected node."""

    def __eq__(self, other: Self) -> bool:
        """CollectionTrees are equal if their children and node attributes are equal."""
        try:
            other_children = other.children
            other_node = other.node
        except AttributeError:
            return NotImplemented
        return self.children == other_children and self.node == other_node

    def __repr__(self) -> str:
        """Indented, multiline representation of the tree to simplify interpreting test failures."""
        if self.children is None:
            children_repr = ""
        else:
            children_repr = indent("\n".join(repr(child).rstrip() for child in self.children), "    ")
        return f"{self.node!r}\n{children_repr}\n"
