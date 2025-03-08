"""
Pytest plugin to collect jupyter Notebooks.

- Identifies all cells which use the `%%ipytest` magic
- adds the notebook, cell and any test functions to the collection tree
- relies on pytest logic and configuration to identify test functions.
"""

from __future__ import annotations

import ast
import importlib.util
import linecache
import os
from types import FunctionType, ModuleType
from typing import TYPE_CHECKING

import _pytest._code
import _pytest.assertion
import _pytest.nodes
import _pytest.pathlib
import pytest

from ._cellpath import CELL_PREFIX, CellPath
from ._parser import Notebook as _ParsedNotebook

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


ipynb2_notebook = pytest.StashKey[_ParsedNotebook]()
ipynb2_cellid = pytest.StashKey[int]()
ipynb2_monkeypatches = pytest.StashKey[dict[tuple[ModuleType, str], FunctionType]]()
"""Original functions indexed by `(module, functionname)` to allow `setattr(module, functionname, original)`."""


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_load_initial_conftests(early_config, parser, args: list[str]) -> Generator[None, None, None]:  # noqa: ANN001, ARG001
    """
    Convert any CellPaths passed as commandline args to "::"-separated nodeids.

    Even though we are using `path/to/notebook.ipynb[Celln]::test_func` as nodeid format, pytest will still accept
    `path/to/notebook.ipynb::Celln::test_func` as a valid nodeid. For unknown reasons,
    `_pytest.main.resolve_collection_argument` removes anything after the first `[`
    """
    # TODO: #50 handle `path/to/notebook.ipynb[Celln]::test_func` in `_pytest.main.resolve_collection_argument`
    # Relying on pytest accepting `path/to/notebook.ipynb::Celln::test_func` as a valid nodeid may be a source of
    # future bugs.

    for idx, arg in enumerate(args):
        if CellPath.is_cellpath(arg.split("::")[0]):
            args[idx] = CellPath.to_nodeid(arg)
    yield


@pytest.hookimpl(tryfirst=True, hookwrapper=True)  # ensure exeution order before any other plugins
def pytest_sessionstart(session: pytest.Session) -> Generator[None, None, None]:
    """Monkeypatch pytest to handle CellPath, store patches in stash to revert later."""
    session.stash[ipynb2_monkeypatches] = CellPath.patch_pytest_absolutepath()
    yield


def pytest_collect_file(file_path: Path, parent: pytest.Collector) -> Notebook | None:
    """Hook implementation to collect jupyter notebooks."""
    if file_path.suffix == ".ipynb":
        nodeid = os.fspath(file_path.relative_to(parent.config.rootpath))
        return Notebook.from_parent(parent=parent, path=file_path, nodeid=nodeid)
    return None


@pytest.hookimpl(tryfirst=True, hookwrapper=True)  # ensure exeution order after any other plugins
def pytest_sessionfinish(session: pytest.Session, exitstatus: int | pytest.ExitCode) -> Generator[None, None, None]:  # noqa: ARG001
    """Revert Monkeypatches based on stashed versions."""
    yield
    for (module, attr), orig in session.stash[ipynb2_monkeypatches].items():
        setattr(module, attr, orig)


class Notebook(pytest.File):
    """A collector for jupyter notebooks."""

    def collect(self) -> Generator[Cell, None, None]:
        """Yield `Cell`s for all cells which contain tests."""
        parsed = _ParsedNotebook(self.path)
        for testcellid in parsed.muggled_testcells.ids():
            name = f"{CELL_PREFIX}{testcellid}"
            nodeid = f"{self.nodeid}[{name}]"
            cell = Cell.from_parent(
                parent=self,
                name=name,
                nodeid=nodeid,
                path=CellPath(f"{self.path}[{name}]"),
            )
            cell.stash[ipynb2_notebook] = parsed
            cell.stash[ipynb2_cellid] = testcellid
            yield cell


class Cell(CellPath.PytestItemMixin, pytest.Module):
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
        - executes all non-test code cells above inside the pseudo-module.__dict__
        - then executes the test cell inside the pseudo-module.__dict__
        - finally adds the test cell to the linecache so that inspect can find the source
        """
        notebook = self.stash[ipynb2_notebook]
        cellid = self.stash[ipynb2_cellid]

        cellsabove = [str(cellsource) for cellsource in notebook.muggled_codecells[:cellid]]
        testcell_source = str(notebook.muggled_testcells[cellid])

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
        linecache.cache[cell_filename] = (0, None, testcell_source.splitlines(keepends=True), cell_filename)
        return dummy_module
