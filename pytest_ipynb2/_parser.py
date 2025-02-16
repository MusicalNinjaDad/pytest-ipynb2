"""Parse notebooks."""

from __future__ import annotations

from typing import TYPE_CHECKING, SupportsIndex, overload

import nbformat

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


class SourceList(list):
    """
    A list with non-continuous indices for storing the contents of cells.

    - supports .keys() analog to a dict, yielding only cell-ids with source.
    - use slicing: sourcelist[:], not list(sourcelist) to get contents.
    """

    def __len__(self) -> int:
        return len([source for source in self if source is not None])

    def keys(self) -> Generator[int, None, None]:
        for key, source in enumerate(self):
            if source is not None:
                yield key

    @overload
    def __getitem__(self, index: SupportsIndex) -> str: ...

    @overload
    def __getitem__(self, index: slice) -> list[str]: ...

    def __getitem__(self, index):
        underlying_list = list(self)
        if isinstance(index, slice):
            return [source for source in underlying_list[index] if source is not None]
        source = underlying_list[index]
        if source is None:
            msg = f"Cell {index} is not present in this SourceList."
            raise IndexError(msg)
        return source


class Notebook:
    """
    An ipython Notebook.

    - constructor from Path
    - methods to get various cell types
    - a `test` cell type identified by the `%%ipytest` cell magic.
    """

    def __init__(self, filepath: Path) -> None:
        contents = nbformat.read(fp=str(filepath), as_version=4)
        nbformat.validate(contents)
        cells = contents.cells
        for cell in cells:
            cell.source = cell.source.splitlines()
        self.codecells = SourceList(
            "\n".join(cell.source) if cell.cell_type == "code" and not cell.source[0].startswith(r"%%ipytest") else None
            for cell in cells
        )
        self.testcells = SourceList(
            "\n".join(cell["source"][1:]).strip()
            if cell.cell_type == "code" and cell.source[0].startswith(r"%%ipytest")
            else None
            for cell in cells
        )

        self.contents: nbformat.NotebookNode = contents

    def getcodecells(self) -> dict[int, str]:
        """Return parsed code cells from a notebook."""
        return {
            cellnr: "\n".join(cell.source)
            for cellnr, cell in enumerate(self.contents.cells)
            if cell.cell_type == "code" and not cell.source[0].startswith(r"%%ipytest")
        }

    def gettestcells(self) -> dict[int, str]:
        """Return parsed test cells from a notebook. Identified by cell magic `%%ipytest`."""
        return {
            cellnr: "\n".join(cell["source"][1:]).strip()
            for cellnr, cell in enumerate(self.contents["cells"])
            if cell["cell_type"] == "code" and cell["source"][0].startswith(r"%%ipytest")
        }
