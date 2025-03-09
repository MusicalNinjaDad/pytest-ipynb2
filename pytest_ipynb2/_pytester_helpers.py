"""Helper classes and functions to support testing this plugin with pytester."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from textwrap import indent
from typing import TYPE_CHECKING, Protocol
from warnings import warn

import nbformat
import pytest

if TYPE_CHECKING:
    from contextlib import suppress
    from types import FunctionType
    from typing import Any

    with suppress(ImportError):
        from typing import Self  # not type-checking on python < 3.11 so don't care if this fails

if sys.version_info < (3, 10):  # dataclass does not offer kw_only on python < 3.10 # pragma: no cover
    _dataclass = dataclass

    def dataclass(*args, **kwargs):  # noqa: ANN002, ANN003
        _ = kwargs.pop("kw_only", None)
        return _dataclass(*args, **kwargs)


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

        Compares equal to a genuine `pytest.Node` if:
            - `isinstance(Node,_DummyNode.nodetype)`
            - `repr(Node)` == `_DummyNode.name`.
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
                sametype = isinstance(other, self.nodetype)
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


class ExampleDir:
    """
    A directory containing example files and the associated pytester instance.

    - `pytester`: pytest.Pytester
    - `path`: pathlib.Path
    - `dir_node`: pytest.Dir
    - `items`: list[pytest.Item]
    """

    pytester: pytest.Pytester
    path: Path | None = None

    def __init__(self, pytester: pytest.Pytester, args: list[str]) -> None:
        self.pytester = pytester
        self.path = self.pytester.path
        self.args = args

    @cached_property
    def dir_node(self) -> pytest.Dir:
        return self.pytester.getpathnode(self.path)

    @cached_property
    def items(self) -> list[pytest.Item]:
        return self.pytester.genitems([self.dir_node])

    @cached_property
    def runresult(self) -> pytest.RunResult:
        return self.pytester.runpytest(*self.args)


@dataclass(kw_only=True)
class ExampleDirSpec:
    """The various elements to set up a pytester instance."""

    path: Path = Path()  # Currently only relevant for notebooks - everything else goes in rootdir
    conftest: str = ""
    ini: str = ""
    files: list[Path] = field(default_factory=list)
    notebooks: dict[str, list[str]] = field(default_factory=dict)
    args: list[str] = field(default_factory=list)

    def __hash__(self) -> int:
        files = tuple(self.files)
        notebooks = tuple((notebook, "\n".join(contents)) for notebook, contents in self.notebooks.items())
        return hash((self.conftest, self.ini, files, notebooks))


class FunctionRequest(Protocol):
    config: pytest.Config
    function: FunctionType
    keywords: dict[str, Any]


class ExampleDirRequest(FunctionRequest):
    param: ExampleDirSpec


@pytest.fixture(scope="module")
def example_dir_cache() -> dict[ExampleDirSpec, ExampleDir]:
    return {}


@pytest.fixture
def example_dir(
    request: ExampleDirRequest,
    pytester: pytest.Pytester,
    example_dir_cache: dict[ExampleDirSpec, ExampleDir],
) -> ExampleDir:
    """Parameterised fixture. Requires a list of `Path`s to copy into a pytester instance."""
    example = request.param
    if (cached_dir := example_dir_cache.get(example)) is None:
        (pytester.path / example.path).mkdir(parents=True, exist_ok=True)
        if example.conftest:
            pytester.makeconftest(request.param.conftest)

        if example.ini:
            pytester.makeini(f"[pytest]\n{example.ini}")

        for filetocopy in example.files:
            pytester.copy_example(str(filetocopy))

        for notebook, contents in example.notebooks.items():
            nbnode = nbformat.v4.new_notebook()
            for cellsource in contents:
                cellnode = nbformat.v4.new_code_cell(cellsource)
                nbnode.cells.append(cellnode)
            nbformat.write(nb=nbnode, fp=pytester.path / example.path / f"{notebook}.ipynb")
        cached_dir = example_dir_cache[example] = ExampleDir(pytester=pytester, args=example.args)
    elif request.config.get_verbosity() >= 3:  # noqa: PLR2004 # pragma: no cover
        # 1st keyword is the test name (incl. any parametrized id)
        msg = f"Using cached {cached_dir.path} for {next(iter(request.keywords))}"
        warn(msg, stacklevel=1)
    return example_dir_cache[example]


def add_ipytest_magic(source: str) -> str:
    """Add %%ipytest magic to the source code."""
    return f"%%ipytest\n\n{source}"


def pytest_configure(config: pytest.Config) -> None:  # pragma: no cover
    # Tests will be needed if this ever becomes public functionality
    """Register autoskip & xfail_for marks."""
    config.addinivalue_line("markers", "autoskip: automatically skip test if expected results not provided")
    config.addinivalue_line("markers", "xfail_for: xfail specified tests dynamically")


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item: pytest.Function) -> None:  # pragma: no cover
    # Tests will be needed if this ever becomes public functionality
    if item.get_closest_marker("autoskip"):
        test_name = item.originalname.removeprefix("test_")
        expected = getattr(item.callspec.getparam("expected_results"), test_name)
        if not expected and expected is not None:
            item.add_marker(pytest.mark.skip(reason="No expected results"))


def pytest_collection_modifyitems(items: list[pytest.Function]) -> None:  # pragma: no cover
    # Tests will be needed if this ever becomes public functionality
    """xfail on presence of a custom marker: `xfail_for(tests:list[str], reasons:list[str])`."""  # noqa: D403
    for item in items:
        test_name = item.originalname.removeprefix("test_")
        if xfail_for := item.get_closest_marker("xfail_for"):
            for xfail_test, reason in xfail_for.kwargs.items():
                if xfail_test == test_name:
                    item.add_marker(pytest.mark.xfail(reason=reason, strict=True))
