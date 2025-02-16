"""Parse notebooks."""

from pathlib import Path

import nbformat


class Cell: ...


class Notebook:
    """
    An ipython Notebook.

    - constructor from Path
    - methods to get various cell types
    - a `test` cell type identified by the `%%ipytest` cell magic.
    """

    def __init__(self, filepath: Path) -> None:
        contents = nbformat.read(fp=str(filepath),as_version=4)
        nbformat.validate(contents)
        for cell in contents.cells:
            cell.source = cell.source.splitlines()
        self.contents = contents

    def getcodecells(self) -> dict[int, str]:
        """Return parsed code cells from a notebook."""
        return {
            cellnr: "\n".join(cell["source"])
            for cellnr, cell in enumerate(self.contents["cells"])
            if cell["cell_type"] == "code" and not cell["source"][0].startswith(r"%%ipytest")
        }

    def gettestcells(self) -> dict[int, str]:
        """Return parsed test cells from a notebook. Identified by cell magic `%%ipytest`."""
        return {
            cellnr: "\n".join(cell["source"][1:]).strip()
            for cellnr, cell in enumerate(self.contents["cells"])
            if cell["cell_type"] == "code" and cell["source"][0].startswith(r"%%ipytest")
        }
