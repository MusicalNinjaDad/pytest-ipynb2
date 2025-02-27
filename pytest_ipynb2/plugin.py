"""
Pytest plugin to collect jupyter Notebooks.

- Identifies all cells which use the `%%ipytest` magic
- adds the notebook, cell and any test functions to the collection tree
- relies on pytest logic and configuration to identify test functions.

Known Issues:

- No Assertion rewriting.
"""

from __future__ import annotations

import ast
import importlib.util
import linecache
from typing import TYPE_CHECKING, Final

import _pytest
import _pytest._code
import _pytest.assertion
import pytest

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path
    from types import ModuleType

from ._parser import Notebook as _ParsedNotebook

ipynb2_notebook = pytest.StashKey[_ParsedNotebook]()
ipynb2_cellid = pytest.StashKey[int]()

CELL_PREFIX: Final[str] = "Cell"
NODE_REGISTRY: Final[str] = "pytest_ipynb2_registry"


class Notebook(pytest.File):
    """A collector for jupyter notebooks."""

    def collect(self) -> Generator[Cell, None, None]:
        """Yield `Cell`s for all cells which contain tests."""
        parsed = _ParsedNotebook(self.path)
        node_registry: set = getattr(self.config, NODE_REGISTRY)
        for testcellid in parsed.testcells.ids():
            name = f"{CELL_PREFIX}{testcellid}"
            nodeid = f"{self.nodeid}::{name}"
            cell = Cell.from_parent(
                parent=self,
                name=name,
                nodeid=nodeid,
                path=self.path,
            )
            cell.stash[ipynb2_notebook] = parsed
            cell.stash[ipynb2_cellid] = testcellid
            node_registry.add(nodeid)
            yield cell


class Cell(pytest.Module):
    """
    A collector for jupyter notebook cells.

    `pytest` will recognise these cells as `pytest.Module`s and use standard collection on them as it would any other
    python module.
    """

    def __repr__(self) -> str:
        """Don't duplicate the word "Cell" in the repr."""
        return f"<{type(self).__name__} {self.stash[ipynb2_cellid]}>"

    def _getobj(self) -> ModuleType:
        notebook = self.stash[ipynb2_notebook]
        cellid = self.stash[ipynb2_cellid]

        cellsabove = notebook.codecells[:cellid]
        testcell_source = notebook.testcells[cellid]

        testcell_ast = ast.parse(testcell_source, filename=str(self.path))
        _pytest.assertion.rewrite.rewrite_asserts(
            mod=testcell_ast,
            source=bytes(testcell_source, encoding="utf-8"),
            module_path=str(self.path),
            config=self.config,
        )

        cell_filename = f"<{self.path}::Cell{cellid}>"
        testcell = compile(testcell_ast, filename=cell_filename, mode="exec")

        dummy_spec = importlib.util.spec_from_loader(f"{self.name}", loader=None)
        dummy_module = importlib.util.module_from_spec(dummy_spec)
        for cell in cellsabove:
            exec(cell, dummy_module.__dict__)  # noqa: S102
        exec(testcell, dummy_module.__dict__)  # noqa: S102
        return dummy_module

    def _reportinfo(self: pytest.Item) -> tuple[str, int, str | None]:
        """Override pytest which checks `.obj.__code__.co_filename` == `.path`."""
        return self.path, 0, "test_fails"

    def collect(self) -> Generator[pytest.Function, None, None]:
        """Replace the reportinfo method on the children, if present."""
        node_registry: set = getattr(self.config, NODE_REGISTRY)

        for item in super().collect():
            node_registry.add(item.nodeid)
            if hasattr(item, "reportinfo"):  # pragma: no branch # TODO(MusicalNinjaDad): #22 Tests grouped in Class
                item.reportinfo = self._reportinfo
            yield item


def pytest_configure(config: pytest.Config) -> None:
    """Add a registry of our objects to the config."""
    setattr(config, NODE_REGISTRY, set())

    def _linecache_getlines_ipynb2(filename: str, module_globals: dict | None = None) -> list[str]:
        if filename.split("::")[0].endswith(".ipynb"):
            return [
                r"#%%ipytest",
                "",
                "def test_fails():",
                "    x = 1",
                "    assert x == 2",
            ]
        return _linecache_getlines_std(filename=filename, module_globals=module_globals)

    _linecache_getlines_std = linecache.getlines
    linecache.getlines = _linecache_getlines_ipynb2

    #TODO: nicer approach probably requires subclassing Path, providing a custom .relativeto and
    # patching _pytest.pathlib.commonpath, which may be helped by a .filepath to strip the ::Celln,
    # it may also be possible (nice, but YAGNI?) to override .__str__ and remove the <> unless that breaks
    # other stuff in pytest that doesn't yet use pathlib but manipulates string paths instead ...
    _pytest._code.code.FormattedExcinfo._makepath = lambda s,p: "failing.ipynb::Cell0"  # noqa: ARG005, SLF001
    #patching _pytest.pathlib.bestrelpath (or _pytest._code.code.bestrelpath) doesn't work
    # the patched code is not called
    
    


def pytest_collect_file(file_path: Path, parent: pytest.Collector) -> Notebook | None:
    """Hook implementation to collect jupyter notebooks."""
    if file_path.suffix == ".ipynb":
        nodeid = file_path.name
        getattr(parent.config, NODE_REGISTRY).add(nodeid)
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
        # call.excinfo.traceback[-1].getsource needs patching. Returns a <_pytest._code.source.Source object>
        pass
