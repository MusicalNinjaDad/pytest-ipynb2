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

    - use slicing: sourcelist[:], not list(sourcelist) to get contents.
    - supports .ids() analog to a mapping.keys(), yielding only cell-ids with source.
    - use .items() analog to a mapping, rather than enumerate().
    """

    def ids(self) -> Generator[int, None, None]:
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
            cell.source = [
                sourceline for sourceline in cell.source.splitlines() if not sourceline.startswith("ipytest")
            ]
        self.codecells = SourceList(
            "\n".join(cell.source)
            if cell.cell_type == "code" and not any(line.startswith(r"%%ipytest") for line in cell.source)
            else None
            for cell in cells
        )
        self.testcells = SourceList(
            "\n".join(line for line in cell.source if not line.startswith(r"%%ipytest")).strip()
            if cell.cell_type == "code" and any(line.startswith(r"%%ipytest") for line in cell.source)
            else None
            for cell in cells
        )
