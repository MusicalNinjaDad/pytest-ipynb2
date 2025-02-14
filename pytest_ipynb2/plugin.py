"""Actual plugin code."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

from ._ipynb_parser import Notebook

ipynb2_notebook = pytest.StashKey[Notebook]()


class NotebookCollector(pytest.File):
    """A pytest `Collector` for jupyter notebooks."""

    def collect(self) -> Generator[NotebookCellCollector, None, None]:
        """Yield NotebookCellCollectors for all cells which contain tests."""
        parsed = Notebook(self.path)
        for testcellid in parsed.gettestcells():
            cell = NotebookCellCollector.from_parent(parent=self, name=f"Cell {testcellid}", path=self.path)
            cell.stash[ipynb2_notebook] = parsed
            yield cell


class NotebookCellCollector(pytest.Collector):
    """A pytest `Collector` for jupyter notebook cells."""

    def collect(self) -> Generator[pytest.Function, None, None]:
        """Yield pytest Functions from within the cell."""


def pytest_collect_file(file_path: Path, parent: pytest.Collector) -> NotebookCollector | None:
    """Hook implementation to collect jupyter notebooks."""
    if file_path.suffix == ".ipynb":
        return NotebookCollector.from_parent(parent=parent, path=file_path)
    return None
