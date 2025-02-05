from pathlib import Path

import pytest


@pytest.fixture
def example_module() -> Path:
    """
    The contents of the code cells in `notebook.ipynb` as a `.py` module.
    
    MUST be added as a fixture BEFORE `pytester`, otherwise it will reference a file in the pytester temp directory.
    """
    return Path("tests/assets/notebook.py").resolve()

def test_collection(example_module: Path, pytester: pytest.Pytester):
    pytester.makepyfile(example_module.read_text())