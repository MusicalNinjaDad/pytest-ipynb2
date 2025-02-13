from pathlib import Path

import pytest
from conftest import CollectedDir


@pytest.mark.parametrize(
        "example_dir",
        [
            pytest.param([Path("tests/assets/notebook.ipynb").absolute()],id="Simple Notebook"),
        ],
)
def test_cell_collected(example_dir:CollectedDir):
    pass