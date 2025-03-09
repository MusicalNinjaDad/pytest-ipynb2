from __future__ import annotations

import sys
import types
from contextlib import suppress
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

import _pytest._code.code
import _pytest.nodes
import _pytest.pathlib

if TYPE_CHECKING:
    from collections.abc import Generator
    from os import PathLike
    from types import FunctionType, ModuleType
    from typing import Any, Final, Self

    import pytest

CELL_PREFIX: Final[str] = "Cell"

if sys.version_info < (3, 12):  # pragma: no cover
    # Can't subclass `pathlib.Path` directly in python < 3.12
    _Path = Path
    Path: Final[type] = type(_Path())


class CellPath(Path):
    """Provide handling of Cells specified as `path/to/file[Celln]`."""

    def __eq__(self, other: object) -> bool:
        """Equality testing handled by `pathlib.Path`."""
        return Path(self) == other

    def __hash__(self) -> int:
        """Hashing handled by `pathlib.Path`."""
        return super().__hash__()

    def exists(self, *args: Any, **kwargs: Any) -> bool:
        """(Only) check that the notebook exists."""
        # TODO: #33 Extend `CellPath.exists` to also check that the cell exists (if performance allows)
        return self.notebook.exists(*args, **kwargs)

    if sys.version_info < (3, 13):  # pragma: no cover

        def relative_to(self, other: PathLike, *args: Any, **kwargs: Any) -> Self:
            """Relative_to only works out-of-the-box on python 3.13 and above."""
            return type(self)(f"{self.notebook.relative_to(other, *args, **kwargs)}[{self.cell}]")

    @cached_property
    def notebook(self) -> Path:
        """Path of the notebook."""
        return self.get_notebookpath(str(self))

    @cached_property
    def cell(self) -> str:
        """The cell specifier (e.g. "Cell0")."""
        return f"{CELL_PREFIX}{self.get_cellid(str(self))}"

    @classmethod
    def is_cellpath(cls, path: str) -> bool:
        """Determine whether a str is a valid representation of our pseudo-path."""
        return path.split(".")[-1].startswith("ipynb") and path.split(f"[{CELL_PREFIX}")[-1].removesuffix("]").isdigit()

    @classmethod
    def get_notebookpath(cls, path: str) -> Path:
        """Return the real path of the notebook based on a pseudo-path."""
        notebookpath = path.split(f"[{CELL_PREFIX}")[0]
        return Path(notebookpath)

    @classmethod
    def get_cellid(cls, path: str) -> int:
        """Return the Cell id from the pseudo-path."""
        cellid = path.split(f"[{CELL_PREFIX}")[-1].removesuffix("]")
        return int(cellid)

    @classmethod
    def to_nodeid(cls, path: str) -> str:
        """
        Convert a pseudo-path to an equivalent nodeid.

        Examples:
            'notebook.ipynb[Cell0]::test_func' -> 'notebook.ipynb::Cell0::test_func'
            'notebook.ipynb[Cell1]' -> 'notebook.ipynb::Cell1'
        """
        cellpath, *nodepath = path.split("::")
        notebookpath = f"{cls.get_notebookpath(cellpath)}"
        cell = f"{CELL_PREFIX}{cls.get_cellid(cellpath)}"
        return "::".join((notebookpath, cell, *nodepath))

    class PytestItemMixin:
        """Provides various overrides to handle our pseudo-path."""

        # TODO: #51 Use metaclass to remove direct references to `CellPath` in `CellPath.PytestItemMixin`
        path: CellPath
        name: str

        def reportinfo(self) -> tuple[Path, int, str]:
            """
            Returns tuple of notebook path, (linenumber=)0, Celln::testname.

            `reportinfo` is used by `location` and included as the header line in the report:
                ```
                ==== FAILURES ====
                ___ reportinfo[2] ___
                ```
            """
            # `nodes.Item.location` calls `absolutepath()` and then `main._node_location_to_relpath` which caches the
            # results in `_bestrelpathcache[node_path]` very early in the test process.
            # As we provide the full CellPath as reportinfo[0] we need to patch `_pytest.nodes.absolutepath` in
            # `CellPath.patch_pytest_pathlib` (above)
            #
            # `TerminalReporter._locationline` adds a `<-` section if `nodeid.split("::")[0] != location[0]`.
            # Verbosity<2 tests runs are grouped by location[0] in the testlog.
            return self.path, 0, f"{self.path.cell}::{self.name}"

        def collect(self) -> Generator[pytest.Function, None, None]:
            """Rebless children to include our overrides from the Mixin."""
            # TODO(MusicalNinjaDad): #22 Handle Tests grouped in Class
            for item in super().collect():  # pytype: disable=attribute-error
                item_type = type(item)
                type_with_mixin = types.new_class(item_type.__name__, (CellPath.PytestItemMixin, item_type))
                item.__class__ = type_with_mixin
                yield item

    @staticmethod
    def patch_pytest_absolutepath() -> dict[tuple[ModuleType, str], FunctionType]:
        """Patch _pytest.pathlib functions."""
        original_functions = {}

        # pytest has some unique handling to get the absolute path of a file. Possbily no longer needed with later
        # versions of pathlib? Hopefully we will be able to remove this patch with a later version of pytest.
        #
        # The original function is defined in _pytest.pathlib but
        # both `code` and `nodes` import it as  `from .pathlib import absolutepath`
        # so we need to patch in both these namespaces...
        _pytest_absolutepath = _pytest.pathlib.absolutepath

        def _absolutepath(path: str | PathLike[str] | Path) -> Path:
            """Return accurate absolute path for string representations of CellPath."""
            # pytype: disable=attribute-error
            try:
                return path.absolute()  # pytest prefers to avoid this, guessing for historical reasons???
            except AttributeError:
                with suppress(AttributeError):  # in case this is not a `str` but some other `PathLike`
                    if CellPath.is_cellpath(path):
                        return CellPath(path).absolute()
            return _pytest_absolutepath(path)
            # pytype: enable=attribute-error

        # 1. `code.Code.path` calls `absolutepath(self.raw.co_filename)` which is the info primarily used in
        #    `TracebackEntry` and therefore relevant for failure reporting.
        original_functions[(_pytest._code.code, "absolutepath")] = _pytest_absolutepath  # noqa: SLF001
        _pytest._code.code.absolutepath = _absolutepath  # noqa: SLF001
        # 2. `nodes.Item.location` calls `absolutepath()` and then `main._node_location_to_relpath` which caches the
        #    results of the `absolutepath()` call in `_bestrelpathcache[node_path]` very early in the test process.
        original_functions[(_pytest.nodes, "absolutepath")] = _pytest_absolutepath
        _pytest.nodes.absolutepath = _absolutepath

        return original_functions
