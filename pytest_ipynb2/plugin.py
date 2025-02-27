"""
Pytest plugin to collect jupyter Notebooks.

- Identifies all cells which use the `%%ipytest` magic
- adds the notebook, cell and any test functions to the collection tree
- relies on pytest logic and configuration to identify test functions.
"""

from __future__ import annotations

import ast
from contextlib import suppress
from functools import cached_property
import importlib.util
import linecache
import os
import types
from typing import TYPE_CHECKING, Any, Final

import _pytest
import _pytest._code
import _pytest.assertion
import _pytest.nodes
import _pytest.pathlib
import pytest

if TYPE_CHECKING:
    from collections.abc import Generator
    from types import ModuleType


from pathlib import Path

from ._parser import Notebook as _ParsedNotebook

ipynb2_notebook = pytest.StashKey[_ParsedNotebook]()
ipynb2_cellid = pytest.StashKey[int]()

CELL_PREFIX: Final[str] = "Cell"


class CellPath(Path):
    """Provide handling of Cells specified as file::Celln."""

    def __str__(self) -> str:
        """Wrap path in <> so stdlib stuff notices it's special."""
        return f"<{super().__str__()}>"

    def __fspath__(self) -> str:
        """Return the path to the notebook."""
        # return str(self.get_notebookpath(str(self)))
        # # _pytest._code.code.Traceback.cut() compares os.fspath(path) with str(code.path) 
        # # so str & __fspath__ must return same value or entry is not identified as relevant.
        return str(self)
    
    def __eq__(self, other: Any) -> bool:
        return Path(self) == other
    
    def __hash__(self):
        return super().__hash__()
    
    def exists(self, *, follow_symlinks = True):
        return self.notebook.exists(follow_symlinks=follow_symlinks)

    @cached_property
    def notebook(self) -> Path:
        """Path of the notebook."""
        return type(self).get_notebookpath(str(self))

    @staticmethod
    def is_cellpath(path: str) -> bool:
        """Determine whether a str is a valid representation of our pseudo-path."""
        return path.startswith("<") and path.endswith(">") and path.split("::")[0].endswith(".ipynb")

    @staticmethod
    def get_notebookpath(path: str) -> Path:
        """Return the real path of the notebook."""
        notebookpath = path.removeprefix("<").split("::")[0]
        return Path(notebookpath)

    @staticmethod
    def get_cellid(path: str) -> int:
        """Return the Cell id from the pseudo-path."""
        cellid = path.removesuffix(">").split("::")[1].removeprefix(CELL_PREFIX)
        return int(cellid)


class IpynbItemMixin:
    """Provides various overrides to handle our pseudo-path."""

    path: Path
    name: str

    def reportinfo(self: pytest.Item) -> tuple[CellPath, int, str]:
        """
        Override pytest which checks `.obj.__code__.co_filename` == `.path`.
        
        `reportinfo` is used by `location` and included as the header line in the report:
            ```
            ==== FAILURES ====
            ___ reportinfo[2] ___
            ```
        """
        return self.path, 0, self.name
    
    # @cached_property
    # def location(self: pytest.Item) -> tuple[CellPath, int, str]:
    #     """
    #     Use pathlib's relative_to not pytests complicated extra logic.

    #     Location[0] is NOT DIRECTLY responsible for the filename in the final line of a test failure report.
    #     But the `nodes.Item` version of it does trigger caching via `main._node_location_to_relpath`
    #     (which uses `main.bestrelpath` and uses `nodes.absolutepath()`.
                
    #     Returns a tuple of ``(relfspath, lineno, testname)`` for this item
    #     where ``relfspath`` is file path relative to ``config.rootpath``
    #     and lineno is a 0-based line number.
    #     """
    #     location: tuple[CellPath, int, str] = self.reportinfo()
    #     # return location[0].relative_to(self.session.config.rootpath), location[1], location[2]
    #     return "FOO", 3, "BAR"


class Notebook(pytest.File):
    """A collector for jupyter notebooks."""

    def collect(self) -> Generator[Cell, None, None]:
        """Yield `Cell`s for all cells which contain tests."""
        parsed = _ParsedNotebook(self.path)
        for testcellid in parsed.testcells.ids():
            name = f"{CELL_PREFIX}{testcellid}"
            nodeid = f"{self.nodeid}::{name}"
            cell = Cell.from_parent(
                parent=self,
                name=name,
                nodeid=nodeid,
                path=CellPath(f"{self.path}::{name}"),
            )
            cell.stash[ipynb2_notebook] = parsed
            cell.stash[ipynb2_cellid] = testcellid
            yield cell


class Cell(IpynbItemMixin, pytest.Module):
    """
    A collector for jupyter notebook cells.

    `pytest` will recognise these cells as `pytest.Module`s and use standard collection on them as it would any other
    python module.
    """

    def __repr__(self) -> str:
        """Don't duplicate the word "Cell" in the repr."""
        return f"<{type(self).__name__} {self.stash[ipynb2_cellid]}>"

    def _getobj(self) -> ModuleType:
        """
        The main magic.

        - loads the cell's source
        - applies assertion rewriting
        - creates a pseudo-module for the cell, with a pseudo-filename
        - executes all non-test code cells above
        - then executes the test cell
        """
        notebook = self.stash[ipynb2_notebook]
        cellid = self.stash[ipynb2_cellid]

        cellsabove = notebook.codecells[:cellid]
        testcell_source = notebook.testcells[cellid]

        cell_filename = str(self.path)

        testcell_ast = ast.parse(testcell_source, filename=cell_filename)
        _pytest.assertion.rewrite.rewrite_asserts(
            mod=testcell_ast,
            source=bytes(testcell_source, encoding="utf-8"),
            module_path=str(self.path),
            config=self.config,
        )

        testcell = compile(testcell_ast, filename=cell_filename, mode="exec")

        dummy_spec = importlib.util.spec_from_loader(f"{self.name}", loader=None)
        dummy_module = importlib.util.module_from_spec(dummy_spec)
        for cell in cellsabove:
            exec(cell, dummy_module.__dict__)  # noqa: S102
        exec(testcell, dummy_module.__dict__)  # noqa: S102
        return dummy_module

    def collect(self) -> Generator[pytest.Function, None, None]:
        """Rebless children to include our overrides from the Mixin."""
        # TODO(MusicalNinjaDad): #22 Handle Tests grouped in Class
        for item in super().collect():
            item_type = type(item)
            ipynbtype = types.new_class(item_type.__name__, (IpynbItemMixin, item_type))
            item.__class__ = ipynbtype
            yield item


def pytest_configure(config: pytest.Config) -> None:  # noqa: ARG001
    """Monkeypatch a few things to cope with us including the Cell in a pseudo-path."""

    def _linecache_getlines_ipynb2(filename: str, module_globals: dict | None = None) -> list[str]:
        if CellPath.is_cellpath(filename):
            notebook = CellPath.get_notebookpath(filename)
            cellid = CellPath.get_cellid(filename)
            return _ParsedNotebook(notebook).testcells[cellid].splitlines()
        return _linecache_getlines_std(filename=filename, module_globals=module_globals)

    _linecache_getlines_std = linecache.getlines
    linecache.getlines = _linecache_getlines_ipynb2

    # TODO: nicer approach probably requires subclassing Path, providing a custom .relativeto and
    # patching _pytest.pathlib.commonpath, which may be helped by a .filepath to strip the ::Celln,
    # it may also be possible (nice, but YAGNI?) to override .__str__ and remove the <> unless that breaks
    # other stuff in pytest that doesn't yet use pathlib but manipulates string paths instead ...

    # _pytest._code.code.FormattedExcinfo._makepath = lambda s, p: "failing.ipynb::Cell0"  # noqa: ARG005, SLF001
    
    _pytest_commonpath = _pytest.pathlib.commonpath

    def _commonpath(path1: CellPath | os.PathLike, path2: CellPath | os.PathLike) -> Path | None:
        """Let pytest handle this with wierd logic, but just give it the notebook path so it can manage."""
        with suppress(AttributeError):
            path1 = path1.notebook
        with suppress(AttributeError):
            path2 = path2.notebook
        return _pytest_commonpath(path1, path2)
    
    _pytest.pathlib.commonpath = _commonpath

    _pytest_absolutepath = _pytest.pathlib.absolutepath
    # _pytest_code_absolutepath = _pytest._code.code.absolutepath

    def _absolutepath(path: str | os.PathLike[str] | Path) -> Path:
        """Return accurate absolute path for string representations of CellPath."""
        try:
            return path.absolute() # pytest prefers to avoid this, guessing for historical reasons???
        except AttributeError:
            with suppress(AttributeError): # in case this is not a `str` but some other `PathLike`
                if CellPath.is_cellpath(path):
                    return CellPath(path.removeprefix("<").removesuffix(">")).absolute()
        return _pytest_absolutepath(path)
    
    # _pytest.pathlib.absolutepath = _absolutepath
    _pytest._code.code.absolutepath = _absolutepath
    _pytest.nodes.absolutepath = _absolutepath

    # patching _pytest.pathlib.bestrelpath (or _pytest._code.code.bestrelpath) doesn't work
    # the patched code is not called
    # patching call.excinfo.traceback[-1].getsource (returns a <_pytest._code.source.Source object>) in
    # pytest_exception_interact showed a bit of promise but hopefully more surgical options are possible


def pytest_collect_file(file_path: Path, parent: pytest.Collector) -> Notebook | None:
    """Hook implementation to collect jupyter notebooks."""
    if file_path.suffix == ".ipynb":
        nodeid = file_path.name
        return Notebook.from_parent(parent=parent, path=file_path, nodeid=nodeid)
    return None


def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> None:  # noqa: ARG001
    """For debugging purposes."""
    if item.nodeid.split("::")[0].endswith(".ipynb"):
        pass


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """For debugging purposes."""
    if report.nodeid.split("::")[0].endswith(".ipynb"):
        pass


def pytest_exception_interact(call: pytest.CallInfo, report: pytest.TestReport) -> None:  # noqa: ARG001
    """For debugging purposes."""
    if report.nodeid.split("::")[0].endswith(".ipynb"):
        pass
