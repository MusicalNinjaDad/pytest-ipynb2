"""Actual plugin code."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path
    from types import ModuleType

from ._ipynb_parser import Notebook as ParsedNotebook

ipynb2_notebook = pytest.StashKey[ParsedNotebook]()


class Notebook(pytest.File):
    """A pytest `Collector` for jupyter notebooks."""

    def collect(self) -> Generator[Cell, None, None]:
        """Yield NotebookCellCollectors for all cells which contain tests."""
        parsed = ParsedNotebook(self.path)
        for testcellid in parsed.gettestcells():
            cell = Cell.from_parent(
                parent=self,
                name=f"Cell {testcellid}",
                nodeid=str(testcellid),
                path=self.path,
            )
            cell.stash[ipynb2_notebook] = parsed
            yield cell


class Cell(pytest.Module):
    """A pytest `Collector` for jupyter notebook cells."""

    def _getobj(self) -> ModuleType:
        notebook = self.stash[ipynb2_notebook]
        cellsource = notebook.gettestcells()[int(self.nodeid)]
        cellspec = importlib.util.spec_from_loader("cell", loader=None)
        cell = importlib.util.module_from_spec(cellspec)
        exec(cellsource, cell.__dict__)  # noqa: S102
        return cell


def pytest_collect_file(file_path: Path, parent: pytest.Collector) -> Notebook | None:
    """Hook implementation to collect jupyter notebooks."""
    if file_path.suffix == ".ipynb":
        return Notebook.from_parent(parent=parent, path=file_path)
    return None
