"""Parse notebooks."""

import json
from pathlib import Path


def getcodecells(notebook: Path) -> dict[int, str]:
    """Return parsed code cells from a notebook."""
    rawcontents = notebook.read_text()
    contents = json.loads(rawcontents)
    return {
        cellnr: "".join(cell["source"])
        for cellnr, cell in enumerate(contents["cells"])
        if cell["cell_type"] == "code" and not cell["source"][0].startswith(r"%%ipytest")
    }

def gettestcells(notebook: Path) -> dict[int, str]:
    """Return parsed test cells from a notebook. Identified by cell magic `%%ipytest`."""
    rawcontents = notebook.read_text()
    contents = json.loads(rawcontents)
    return {
        cellnr: "".join(cell["source"][1:]).strip()
        for cellnr, cell in enumerate(contents["cells"])
        if cell["cell_type"] == "code" and cell["source"][0].startswith(r"%%ipytest")
    }