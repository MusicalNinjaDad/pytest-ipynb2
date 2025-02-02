from pathlib import Path

from pytest_ipynb2 import getcodecells

testnotebook = Path("tests/assets/notebook.ipynb")

def test_codecells():
    codecells = getcodecells(testnotebook)
    assert len(codecells) == 3