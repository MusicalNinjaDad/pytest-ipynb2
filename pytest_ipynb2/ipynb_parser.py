"""Parse notebooks."""

import json
from pathlib import Path


def getcodecells(notebook: Path) -> list[dict]:
    """Return parsed code cells from a notebook."""
    rawcontents = notebook.read_text()
    contents = json.loads(rawcontents)
    return [cell for cell in contents["cells"] if cell["cell_type"] == "code"]