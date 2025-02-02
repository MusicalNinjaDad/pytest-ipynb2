"""Parse notebooks."""

import json
from pathlib import Path


def getcodecells(notebook: Path) -> dict[dict]:
    """Return parsed code cells from a notebook."""
    rawcontents = notebook.read_text()
    contents = json.loads(rawcontents)
    return {cellnr: cell for cellnr, cell in enumerate(contents["cells"]) if cell["cell_type"] == "code"}