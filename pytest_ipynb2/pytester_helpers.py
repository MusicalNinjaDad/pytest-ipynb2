"""Helper classes and functions to support testing this plugin with pytester."""

from __future__ import annotations

from dataclasses import dataclass
from textwrap import indent
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from contextlib import suppress
    from pathlib import Path

    with suppress(ImportError):  # not type-checking on python < 3.11
        from typing import Self


class CollectionTree:
    """
    A (top-down) tree of pytest collection Nodes.

    Designed to enable testing the results of collection plugins via:
    ```
    assert CollectionTree.from_items(pytester.genitems([...])) == CollectionTree.from_dict({...})
    ```
    """

    @classmethod
    def from_items(cls, items: list[pytest.Item]) -> Self:
        """
        Create a single CollectionTree from a list of collected `Items`.

        It is intended that this function is passed the result of `pytester.genitems()`

        Returns: a CollectionTree with the Session as the root.
        """
        if not items:
            # If we don't specifically handle this here, then `all([])` returns `True` in _walk_up_tree
            msg = "Items list is empty."
            raise ValueError(msg)

        return cls._walk_up_tree([cls(node=item, children=None) for item in items])

    @classmethod
    def _walk_up_tree(cls, branches: list[Self]) -> Self:
        """
        Walk up the collection tree from a list of branches/leaves until reaching the `pytest.Session`.

        Returns: the Session `CollectionTree`.
        """
        parents = (branch.node.parent for branch in branches)
        branches_byparent = {
            parent: [branch for branch in branches if branch.node.parent == parent]
            for parent in parents
        }  # fmt: skip
        parent_trees = [cls(node=parent, children=list(children)) for parent, children in branches_byparent.items()]

        if all(isinstance(parent.node, pytest.Session) for parent in parent_trees):
            assert len(parent_trees) == 1, "We should only ever have one Session."  # noqa: S101
            return next(iter(parent_trees))

        return cls._walk_up_tree(parent_trees)

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
        tree = CollectionTree.from_dict(tree_dict)
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
            )  # fmt:skip

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
        """Always `None` but required to avoid attribute errors if type checking `Union[pytest.Node,_DummyNode]`"""

        def __eq__(self, other: pytest.Item | pytest.Collector | Self) -> bool:
            try:
                samename = self.name == other.name
                sametype = self.nodetype == other.nodetype
            except AttributeError:
                samename = self.name == repr(other)
                sametype = self.nodetype is type(other)
            return samename and sametype

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


@dataclass
class CollectedDir:
    """
    The various elements required to test directory collection.

    - `pytester_instance`: pytest.Pytester
    - `dir_node`: pytest.Dir
    - `items`: list[pytest.Item]
    """

    pytester_instance: pytest.Pytester
    dir_node: pytest.Dir
    items: list[pytest.Item]


@dataclass
class ExampleDir:
    """The various elements to set up a pytester instance."""

    files: list[Path]
    conftest: str = ""
