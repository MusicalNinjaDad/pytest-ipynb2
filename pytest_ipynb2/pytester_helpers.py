"""Helper classes and functions to support testing this plugin with pytester."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from textwrap import indent
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from contextlib import suppress

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
        """Create a CollectionTree from a list of collection items, as returned by `pytester.genitems()`."""

        def _from_item(item: pytest.Item | Self) -> Self:
            return item if isinstance(item, cls) else cls(node=item, children=None)

        def _get_parents_as_CollectionTrees(items: list[Self]) -> list[Self]:  # noqa: N802
            """Returns a list of CollectionTree items for the parents of those provided."""
            parents = (item.node.parent for item in items)
            items_byparent = {
                parent: [item for item in items if item.node.parent == parent]
                for parent in parents
            }  # fmt: skip
            return [cls(node=parent, children=list(children)) for parent, children in items_byparent.items()]

        if not items:
            # If we don't specifically handle this here, then `all([])` returns `True` later and wierd stuff happens
            msg = "Items list is empty."
            raise ValueError(msg)

        items = [_from_item(item) for item in items]

        if all(isinstance(item.node, pytest.Session) for item in items):
            assert len(items) == 1, "There should only ever be one session node."  # noqa: S101
            return next(iter(items))

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
