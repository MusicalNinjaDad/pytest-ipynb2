"""Parse notebooks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self, SupportsIndex, overload

import nbformat

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


class SourceList(list):
    """
    A `list` with non-continuous indices for storing the contents of cells.

    - use a full slice `sourcelist[:]`, not list(sourcelist) to get contents.
    - supports `.ids()` analog to a mapping.keys(), yielding only cell-ids with source.
    """

    def ids(self) -> Generator[int, None, None]:
        """Analog to mapping `.keys()`, yielding only cell-ids with source."""
        for key, source in enumerate(self):
            if source is not None:
                yield key

    @overload
    def __getitem__(self, index: SupportsIndex) -> str: ...

    @overload
    def __getitem__(self, index: slice) -> list[str]: ...

    def __getitem__(self, index):
        """
        Behaves as you would expect for a `list` with the following exceptions.

        - If provided with a single `index`: Raises an IndexError if the element at `index` does not
            contain any relevant source.
        - If provided with a `slice`: Returns only those items, which contain relevant source.

        """
        underlying_list = list(self)
        if isinstance(index, slice):
            return [source for source in underlying_list[index] if source is not None]
        source = underlying_list[index]
        if source is None:
            msg = f"Cell {index} is not present in this SourceList."
            raise IndexError(msg)
        return source

    def muggle(self) -> Self:
        """Comment out any ipython magics."""

        def _muggleentry(source: str) -> str:
            if source is None:
                return None
            muggled = [
                f"# {line}" if (line.strip().startswith("%") or line.strip().startswith("ipytest")) else line
                for line in source.splitlines()
            ]
            return "\n".join(muggled)

        return type(self)([_muggleentry(source) for source in list(self)])


class Notebook:
    """
    The relevant bits of an ipython Notebook.

    Attributes:
        codecells (SourceList): The code cells *excluding* any identified as test cells.
        testcells (SourceList): The code cells which are identified as containing tests, based
            upon the presence of the `%%ipytest`magic.
    """

    def __init__(self, filepath: Path) -> None:
        self.codecells: SourceList
        """The code cells *excluding* any identified as test cells"""
        self.testcells: SourceList
        """The code cells which are identified as containing tests, based upon the presence of the `%%ipytest`magic."""

        contents = nbformat.read(fp=str(filepath), as_version=4)
        nbformat.validate(contents)
        cells: list[Cell] = contents.cells

        for cell in cells:
            cell.source = cell.source.splitlines()

        def _istestcell(source: list[str]) -> bool:
            return any(line.strip().startswith(r"%%ipytest") for line in source)

        self.codecells = SourceList(
            "\n".join(cell.source) if cell.cell_type == "code" and not _istestcell(cell.source) else None
            for cell in cells
        )
        """The code cells *excluding* any identified as test cells"""
        self.testcells = SourceList(
            "\n".join(cell.source) if cell.cell_type == "code" and _istestcell(cell.source) else None for cell in cells
        ).muggle()
        """The code cells which are identified as containing tests, based upon the presence of the `%%ipytest`magic."""

class Cell(Protocol):
    source: str
    cell_type: str