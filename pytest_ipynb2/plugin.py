"""
Pytest plugin to collect jupyter Notebooks.

- Identifies all cells which use the `%%ipytest` magic
- adds the notebook, cell and any test functions to the collection tree
- relies on pytest logic and configuration to identify test functions.

Known Issues:

- Pytest output to stdout does not properly list the tests or apply Assertion rewriting.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path
    from types import ModuleType

from ._parser import Notebook as _ParsedNotebook

ipynb2_notebook = pytest.StashKey[_ParsedNotebook]()


class Notebook(pytest.File):
    """A collector for jupyter notebooks."""

    def collect(self) -> Generator[Cell, None, None]:
        """Yield `Cell`s for all cells which contain tests."""
        parsed = _ParsedNotebook(self.path)
        for testcellid in parsed.testcells.ids():
            cell = Cell.from_parent(
                parent=self,
                name=str(testcellid),
                nodeid=f"{self.path.name}::{testcellid}",
                path=self.path,
            )
            cell.stash[ipynb2_notebook] = parsed
            yield cell


class Cell(pytest.Module):
    """
    A collector for jupyter notebook cells.

    `pytest` will recognise these cells as `pytest.Module`s and use standard collection on them as it would any other
    python module.
    """

    def _getobj(self) -> ModuleType:
        notebook = self.stash[ipynb2_notebook]
        cellid = int(self.name)
        cellsabove = "\n".join(notebook.codecells[:cellid])
        testcell = notebook.testcells[cellid]
        dummy_spec = importlib.util.spec_from_loader(f"Cell{self.name}", loader=None)
        dummy_module = importlib.util.module_from_spec(dummy_spec)
        exec(f"{cellsabove}\n{testcell}", dummy_module.__dict__)  # noqa: S102
        return dummy_module


def pytest_collect_file(file_path: Path, parent: pytest.Collector) -> Notebook | None:
    """Hook implementation to collect jupyter notebooks."""
    if file_path.suffix == ".ipynb":
        return Notebook.from_parent(parent=parent, path=file_path)
    return None
