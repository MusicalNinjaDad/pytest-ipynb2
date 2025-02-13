"""Actual plugin code."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

from ._ipynb_parser import Notebook


class NotebookCollector(pytest.File):
    """A pytest `Collector` for jupyter notebooks."""

    def collect(self) -> Generator[NotebookCellCollector, None, None]:
        """Return NotebookCellCollectors for all cells which contain tests."""
        parsed = Notebook(self.path)
        for testcell in parsed.gettestcells():
            yield NotebookCellCollector.from_parent(parent=self, name=f"Cell {testcell}")

class NotebookCellCollector(pytest.Class):
    """A pytest `Collector` for jupyter notebook cells."""

    def collect(self) -> pytest.Function: ...  # noqa: D102



def pytest_collect_file(file_path: Path, parent: pytest.Collector) -> NotebookCollector | None:
    """Hook implementation to collect jupyter notebooks."""
    if file_path.suffix == ".ipynb":
        return NotebookCollector.from_parent(parent=parent, path=file_path)
    return None
