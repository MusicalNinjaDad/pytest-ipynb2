"""Parse notebooks."""

from __future__ import annotations

import ast
from functools import cached_property
from typing import TYPE_CHECKING, Protocol, overload

import IPython.core.inputtransformer2
import nbformat

if TYPE_CHECKING:
    from collections.abc import Collection, Generator, Iterator, Sequence
    from contextlib import suppress
    from pathlib import Path
    from typing import SupportsIndex

    with suppress(ImportError):  # not type-checking on python < 3.11
        from typing import Self


class MagicFinder(ast.NodeVisitor):
    """Identifies lines which use ipython magics or call ipytest."""

    def __init__(self) -> None:
        self.magiclines: set[int] = set()
        """Linenumbers (starting at 1) of lines containing magics/ipytest."""
        self.magicnames = {"get_ipython", "ipytest"}
        super().__init__()

    def visit_Call(self, node: ast.Call):  # noqa: N802
        if getattr(node.func, "id", None) in self.magicnames:
            self.magiclines.add(node.lineno)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):  # noqa: N802
        if getattr(node.value, "id", None) in self.magicnames:
            self.magiclines.add(node.lineno)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):  # noqa: N802
        for mod in node.names:
            if mod.name == "ipytest":
                self.magiclines.add(node.lineno)
                if mod.asname is not None:
                    self.magicnames.add(mod.asname)
                break
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):  # noqa: N802
        if node.module in self.magicnames:
            self.magiclines.add(node.lineno)
            for attr in node.names:
                self.magicnames.add(attr.asname if attr.asname is not None else attr.name)
        self.generic_visit(node)


class CellSource:
    """
    Contains source code of a ipynb cell.

    - Initialisable either from a multiline string, or a sequence of strings (one per line)
    - String representation is multiline string
    - Iterates by line
    """

    def __init__(self, contents: Sequence[str] | str):
        self._string = contents if isinstance(contents, str) else "\n".join(contents)

    def __str__(self) -> str:
        return self._string

    def __eq__(self, other: object) -> bool:
        return str(self) == str(other)

    def __hash__(self) -> int:
        return hash(self._string)  # pragma: no cover

    def __iter__(self) -> Iterator[str]:
        return iter(self._string.splitlines())

    @property
    def cellmagiclines(self) -> set[int]:
        """Return a new CellSource with any lines containing cellmagics commented out."""
        return {lineno for lineno, line in enumerate(self, start=1) if line.strip().startswith(r"%%")}

    @property
    def magiclines(self) -> set[int]:
        """Return a list of all lines (starting at 1), the `MagicFinder` identifies."""
        transformer = IPython.core.inputtransformer2.TransformerManager()
        finder = MagicFinder()
        transformed = transformer.transform_cell(str(self))
        tree = ast.parse(str(transformed))
        finder.visit(tree)
        return finder.magiclines

    def commentout(self, lines: Collection[int]) -> Self:
        return type(self)([f"# {line}" if lineno in lines else line for lineno, line in enumerate(self, start=1)])

    @cached_property
    def muggled(self) -> Self:
        """A version of this `Source` with magic (and ipytest) lines commented out."""
        # Need to handle cell magics first otherwise ipython transformer
        # munges the whole cell into a single `run_cell_magic` line
        nocellmagics = self.commentout(self.cellmagiclines)
        return nocellmagics.commentout(nocellmagics.magiclines)


class SourceList(list[CellSource]):
    """
    A `list[CellSource]` with non-continuous indices for storing the contents of cells.

    - use a full slice `sourcelist[:]`, not list(sourcelist) to get contents.
    - supports `.ids()` analog to a mapping.keys(), yielding only cell-ids with source.
    """

    def ids(self) -> Generator[int, None, None]:
        """Analog to mapping `.keys()`, yielding only cell-ids with source."""
        for key, source in enumerate(self):
            if source is not None:
                yield key

    @overload
    def __getitem__(self, index: SupportsIndex) -> CellSource: ...

    @overload
    def __getitem__(self, index: slice) -> list[CellSource]: ...

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
        muggled_codecells (SourceList): The code cells *excluding* any identified as test cells.
            With magic & ipytest lines commented out.
        muggled_testcells (SourceList): The code cells which are identified as containing tests,
            based upon the presence of the `%%ipytest` magic. With magic & ipytest lines commented out.
    """

    def __init__(self, filepath: Path) -> None:
        self.muggled_codecells: SourceList
        """The code cells *excluding* any identified as test cells. With magic & ipytest lines commented out."""
        self.muggled_testcells: SourceList
        """
        The code cells which are identified as containing tests, based upon the presence of the `%%ipytest`magic.
        With magic & ipytest lines commented out.
        """

        contents = nbformat.read(fp=str(filepath), as_version=4)
        nbformat.validate(contents)
        cells: list[Cell] = contents.cells

        for cell in cells:
            cell.source = CellSource(cell.source)  # type: ignore[attr-defined]  # fulfils protocol after this conversion

        def _istestcell(cell: Cell) -> bool:
            return cell.cell_type == "code" and any(line.strip().startswith(r"%%ipytest") for line in cell.source)

        def _iscodecell(cell: Cell) -> bool:
            return cell.cell_type == "code"

        self.muggled_codecells = SourceList(
            cell.source.muggled if _iscodecell(cell) and not _istestcell(cell) else None for cell in cells
        )
        self.muggled_testcells = SourceList(cell.source.muggled if _istestcell(cell) else None for cell in cells)


class Cell(Protocol):
    source: CellSource
    cell_type: str
