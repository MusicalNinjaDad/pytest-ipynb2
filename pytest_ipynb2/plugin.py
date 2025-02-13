"""Actual plugin code."""

from pathlib import Path

import pytest


class NotebookCollector(pytest.File):
    """A pytest `Collector` for jupyter notebooks."""

    def collect(): ...  # noqa: ANN201, D102


def pytest_collect_file(file_path: Path, parent: pytest.Collector) -> NotebookCollector:
    """Hook implementation to collect jupyter notebooks."""
    if file_path.suffix == ".ipynb":
        return NotebookCollector.from_parent(parent=parent, path=file_path)
    return None
