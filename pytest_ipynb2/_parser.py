"""Parse notebooks."""

from __future__ import annotations

import ast
from functools import cached_property
from typing import TYPE_CHECKING, Protocol, overload

import IPython.core.inputtransformer2
import nbformat

if TYPE_CHECKING:
    from collections.abc import Generator, Iterator, Sequence
    from contextlib import suppress
    from pathlib import Path
    from typing import SupportsIndex

    with suppress(ImportError):  # not type-checking on python < 3.11
        from typing import Self


class MagicFinder(ast.NodeVisitor):
    def __init__(self):
        self.magiclines = set()
        self.magicnames = {"get_ipython", "ipytest"}
        super().__init__()

    def visit_Call(self, node: ast.Call):
        if getattr(node.func, "id", None) in self.magicnames:
            self.magiclines.add(node.lineno)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        if getattr(node.value, "id", None) in self.magicnames:
            self.magiclines.add(node.lineno)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for mod in node.names:
            if mod.name == "ipytest":
                self.magiclines.add(node.lineno)
                if mod.asname is not None:
                    self.magicnames.add(mod.asname)
                break
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module in self.magicnames:
            self.magiclines.add(node.lineno)
            for attr in node.names:
                self.magicnames.add(attr.asname if attr.asname is not None else attr.name)
        self.generic_visit(node)


class Source:
    def __init__(self, contents: Sequence[str] | str):
        if isinstance(contents, str):
            self._string = contents
        else:
            self._string = "\n".join(contents)

    def __str__(self) -> str:
        return self._string

    def __eq__(self, other: object) -> bool:
        return str(self) == str(other)

    def __hash__(self) -> int:
        return hash(self._string)

    def __iter__(self) -> Iterator[str]:
        return iter(self._string.splitlines())

    def muggle_cellmagics(self) -> Self:
        newcontents = [f"# {line}" if line.strip().startswith(r"%%") else line for line in self]
        return type(self)(newcontents)
    
    def find_magiclines(self) -> set[int]:
        transformer = IPython.core.inputtransformer2.TransformerManager()
        finder = MagicFinder()
        transformed = transformer.transform_cell(str(self))
        tree = ast.parse(str(transformed))
        finder.visit(tree)
        return finder.magiclines
    
    @cached_property
    def muggled(self) -> Self:
        nocellmagics = self.muggle_cellmagics()
        linestomuggle = nocellmagics.find_magiclines()
        muggledlines = [
                    f"# {line}" if lineno in linestomuggle else line
                    for lineno, line in enumerate(nocellmagics, start=1)
                ]
        return type(self)(muggledlines)

class SourceList(list[Source]):
    """
    A `list[Source]` with non-continuous indices for storing the contents of cells.

    - use a full slice `sourcelist[:]`, not list(sourcelist) to get contents.
    - supports `.ids()` analog to a mapping.keys(), yielding only cell-ids with source.
    """

    def ids(self) -> Generator[int, None, None]:
        """Analog to mapping `.keys()`, yielding only cell-ids with source."""
        for key, source in enumerate(self):
            if source is not None:
                yield key

    @overload
    def __getitem__(self, index: SupportsIndex) -> Source: ...

    @overload
    def __getitem__(self, index: slice) -> list[Source]: ...

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
            cell.source = cell.source.splitlines()  # type: ignore[attr-defined]  # fulfils protocol after splitlines

        def _istestcell(cell: Cell) -> bool:
            return cell.cell_type == "code" and any(line.strip().startswith(r"%%ipytest") for line in cell.source)

        def _iscodecell(cell: Cell) -> bool:
            return cell.cell_type == "code"

        self.codecells = SourceList(
            Source(cell.source).muggled if _iscodecell(cell) and not _istestcell(cell) else None for cell in cells
        )
        self.testcells = SourceList(Source(cell.source).muggled if _istestcell(cell) else None for cell in cells)


class Cell(Protocol):
    source: list[str]
    cell_type: str
