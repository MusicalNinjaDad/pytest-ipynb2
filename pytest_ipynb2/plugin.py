"""
Pytest plugin to collect jupyter Notebooks.

- Identifies all cells which use the `%%ipytest` magic
- adds the notebook, cell and any test functions to the collection tree
- relies on pytest logic and configuration to identify test functions.
"""

from __future__ import annotations

import ast
import importlib.util
import linecache
import logging
import os
import sys
import types
from contextlib import suppress
from functools import cached_property
from pathlib import Path
from types import FunctionType, ModuleType
from typing import TYPE_CHECKING, Any, Final

import _pytest._code
import _pytest.assertion
import _pytest.nodes
import _pytest.pathlib
import pytest

from ._parser import Notebook as _ParsedNotebook

if TYPE_CHECKING:
    from collections.abc import Generator
    from os import PathLike

    with suppress(ImportError):
        from typing import Self

if sys.version_info < (3, 12):  # pragma: no cover
    _Path = Path
    Path: Final[type] = type(_Path())


ipynb2_notebook = pytest.StashKey[_ParsedNotebook]()
ipynb2_cellid = pytest.StashKey[int]()
ipynb2_monkeypatches = pytest.StashKey[dict[tuple[ModuleType, str], FunctionType]]()

CELL_PREFIX: Final[str] = "Cell"

log = logging.getLogger(__name__)

@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:
    """Set up logging for the plugin."""
    log.debug("==pytest_configure finished==")
    log.debug("Plugin configured with pytest %s", config.option.version)
    log.debug("Plugins activated: %s", config.pluginmanager.list_plugin_distinfo())
    log.debug("Working directory: %s", Path.cwd())


class CellPath(Path):
    """Provide handling of Cells specified as `path/to/file[Celln]`."""

    def __str__(self) -> str:
        """Wrap path in <> so `inspect.getsource` notices it's special."""
        return f"<{super().__str__()}>"

    def __fspath__(self) -> str:
        """Return the same as `str` due to pytest wierdness."""
        # TODO: #32 Change `CellPath.__fspath__` to return path to notebook when pytest fixes their path handling.
        # Ideally we would `return str(self.get_notebookpath(str(self)))` here but ...
        # `_pytest._code.code.Traceback.cut()` compares `os.fspath(path)` with `str(code.path)`
        # so `str` & `__fspath__` must return same value or the TracebackEntry is not identified
        # as relevant and we end up with the full unfiltered traceback on test failures.
        return str(self)

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
            return type(self)(f"{self.notebook.relative_to(other, *args, **kwargs)}::{self.cell}")

    @cached_property
    def notebook(self) -> Path:
        """Path of the notebook."""
        return type(self).get_notebookpath(str(self))

    @cached_property
    def cell(self) -> str:
        """The cell specifier (e.g. "Cell0")."""
        return f"{CELL_PREFIX}{type(self).get_cellid(str(self))}"

    @staticmethod
    def is_cellpath(path: str) -> bool:
        """Determine whether a str is a valid representation of our pseudo-path."""
        return (
            path.startswith("<")
            and path.endswith(">")
            and path.split(".")[-1].startswith("ipynb")
            and path.split(f"[{CELL_PREFIX}")[-1].removesuffix("]>").isdigit()
        )

    @classmethod
    def get_notebookpath(cls, path: str) -> Path:
        """Return the real path of the notebook based on a pseudo-path."""
        notebookpath = path.removeprefix("<").split(f"[{CELL_PREFIX}")[0]
        return Path(notebookpath)

    @classmethod
    def get_cellid(cls, path: str) -> int:
        """Return the Cell id from the pseudo-path."""
        cellid = path.split(f"[{CELL_PREFIX}")[-1].removesuffix("]>")
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

    @staticmethod
    def patch_linecache() -> dict[tuple[ModuleType, str], FunctionType]:
        """Patch linecache.getlines to handle CellPaths (like doctest does)."""
        original_functions = {}

        original_functions[linecache, "getlines"] = _linecache_getlines_std = linecache.getlines

        def _linecache_getlines_ipynb2(filename: str, module_globals: dict | None = None) -> list[str]:
            if CellPath.is_cellpath(filename):
                notebook = CellPath.get_notebookpath(filename)
                cellid = CellPath.get_cellid(filename)
                return list(_ParsedNotebook(notebook).muggled_testcells[cellid])
            return _linecache_getlines_std(filename=filename, module_globals=module_globals)

        linecache.getlines = _linecache_getlines_ipynb2

        return original_functions

    @staticmethod
    def patch_pytest_pathlib() -> dict[tuple[ModuleType, str], FunctionType]:
        """Patch _pytest.pathlib functions."""
        original_functions = {}

        original_functions[(_pytest.pathlib, "commonpath")] = _pytest_commonpath = _pytest.pathlib.commonpath

        def _commonpath(path1: CellPath | os.PathLike, path2: CellPath | os.PathLike) -> Path | None:
            """Let pytest handle this with wierd logic, but just give it the notebook path so it can manage."""
            # pytype: disable=attribute-error
            with suppress(AttributeError):
                path1 = path1.notebook
            with suppress(AttributeError):
                path2 = path2.notebook
            # pytype: enable=attribute-error
            return _pytest_commonpath(path1, path2)

        _pytest.pathlib.commonpath = _commonpath

        # pytest has some unique handling to get the absolute path of a file. Possbily no longer needed with later
        # versions of pathlib? Hopefully we will be able to remove this patch with a later version of pytest.
        #
        # The original function is defined in _pytest.pathlib but
        # both `code` and `nodes` import it as  `from .pathlib import absolutepath`
        # so we need to patch in both these namespaces...
        _pytest_absolutepath = _pytest.pathlib.absolutepath

        def _absolutepath(path: str | os.PathLike[str] | Path) -> Path:
            """Return accurate absolute path for string representations of CellPath."""
            # pytype: disable=attribute-error
            try:
                return path.absolute()  # pytest prefers to avoid this, guessing for historical reasons???
            except AttributeError:
                with suppress(AttributeError):  # in case this is not a `str` but some other `PathLike`
                    if CellPath.is_cellpath(path):
                        return CellPath(path.removeprefix("<").removesuffix(">")).absolute()
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


class IpynbItemMixin:
    """Provides various overrides to handle our pseudo-path."""

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


class Notebook(pytest.File):
    """A collector for jupyter notebooks."""

    def collect(self) -> Generator[Cell, None, None]:
        """Yield `Cell`s for all cells which contain tests."""
        parsed = _ParsedNotebook(self.path)
        for testcellid in parsed.muggled_testcells.ids():
            name = f"{CELL_PREFIX}{testcellid}"
            nodeid = f"{self.nodeid}[{name}]"
            cell = Cell.from_parent(
                parent=self,
                name=name,
                nodeid=nodeid,
                path=CellPath(f"{self.path}[{name}]"),
            )
            cell.stash[ipynb2_notebook] = parsed
            cell.stash[ipynb2_cellid] = testcellid
            yield cell


class Cell(IpynbItemMixin, pytest.Module):
    """
    A collector for jupyter notebook cells.

    `pytest` will recognise these cells as `pytest.Module`s and use standard collection on them as it would any other
    python module.
    """

    def __repr__(self) -> str:
        """Don't duplicate the word "Cell" in the repr."""
        return f"<{type(self).__name__} {self.stash[ipynb2_cellid]}>"

    def _getobj(self) -> ModuleType:
        """
        The main magic.

        - loads the cell's source
        - applies assertion rewriting
        - creates a pseudo-module for the cell, with a pseudo-filename
        - executes all non-test code cells above
        - then executes the test cell
        """
        notebook = self.stash[ipynb2_notebook]
        cellid = self.stash[ipynb2_cellid]

        cellsabove = [str(cellsource) for cellsource in notebook.muggled_codecells[:cellid]]
        testcell_source = str(notebook.muggled_testcells[cellid])

        cell_filename = str(self.path)

        testcell_ast = ast.parse(testcell_source, filename=cell_filename)
        _pytest.assertion.rewrite.rewrite_asserts(
            mod=testcell_ast,
            source=bytes(testcell_source, encoding="utf-8"),
            module_path=str(self.path),
            config=self.config,
        )

        testcell = compile(testcell_ast, filename=cell_filename, mode="exec")

        dummy_spec = importlib.util.spec_from_loader(f"{self.name}", loader=None)
        dummy_module = importlib.util.module_from_spec(dummy_spec)
        for cell in cellsabove:
            exec(cell, dummy_module.__dict__)  # noqa: S102
        exec(testcell, dummy_module.__dict__)  # noqa: S102
        return dummy_module

    def collect(self) -> Generator[pytest.Function, None, None]:
        """Rebless children to include our overrides from the Mixin."""
        # TODO(MusicalNinjaDad): #22 Handle Tests grouped in Class
        log.debug("==Collecting from cell: %s==", self.name)
        log.debug("Module content: %s", self.obj.__dict__.keys())
        for item in super().collect():
            item_type = type(item)
            log.debug("Found: %s (%s)", item.name, item_type)
            type_with_mixin = types.new_class(item_type.__name__, (IpynbItemMixin, item_type))
            item.__class__ = type_with_mixin
            log.debug("Reblessed to: %s", item.__class__)
            yield item
        log.debug("==Finished collecting from cell: %s==", self.name)


def pytest_sessionstart(session: pytest.Session) -> None:
    """Monkeypatch a few things to handle CellPath."""
    session.stash[ipynb2_monkeypatches] = CellPath.patch_linecache()
    session.stash[ipynb2_monkeypatches] |= CellPath.patch_pytest_pathlib()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int | pytest.ExitCode) -> None:  # noqa: ARG001
    """Revert Monkeypatches - for complete safety."""
    for (module, attr), orig in session.stash[ipynb2_monkeypatches].items():
        setattr(module, attr, orig)


def pytest_collect_file(file_path: Path, parent: pytest.Collector) -> Notebook | None:
    """Hook implementation to collect jupyter notebooks."""
    if file_path.suffix == ".ipynb":
        nodeid = os.fspath(file_path.relative_to(parent.config.rootpath))
        return Notebook.from_parent(parent=parent, path=file_path, nodeid=nodeid)
    return None


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_load_initial_conftests(early_config, parser, args: list[str]) -> Generator[None, None, None]:  # noqa: ANN001, ARG001
    """Convert any CellPaths passed as commandline args to nodeids."""
    log = logging.getLogger(__name__)
    
    # Use workspace directory for logs
    WORKSPACE_DIR = Path(os.getenv("WORKSPACE_DIR", Path.cwd()))  # noqa: N806
    log_dir = WORKSPACE_DIR / ".logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler(log_dir / "pytest_ipynb2.log")
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        ),
    )
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)
    
    log.debug("==pytest_load_initial_conftests started==")
    log.debug("Original command line args: %s", args)
    for idx, arg in enumerate(args):
        if CellPath.is_cellpath(arg.split("::")[0]):
            args[idx] = CellPath.to_nodeid(arg)
    log.debug("Updated command line args: %s", args)
    yield
    log.debug("==pytest_load_initial_conftests finished==")
    log.debug("Config: %s", early_config)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_cmdline_parse(pluginmanager: pytest.PytestPluginManager, args: list[str]) -> Generator[None, None, None]:
    """Add logging for command line parsing."""
    log.debug("==pytest_cmdline_parse started==")
    log.debug("Command line args: %s", args)
    log.debug("Plugin manager: %s", pluginmanager.list_plugin_distinfo())
    yield
    log.debug("==pytest_cmdline_parse finished==")
    log.debug("Command line args: %s", args)
    log.debug("Plugin manager: %s", pluginmanager.list_plugin_distinfo())
