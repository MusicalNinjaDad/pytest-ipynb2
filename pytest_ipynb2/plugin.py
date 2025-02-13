"""Actual plugin code."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


class NotebookCollector(pytest.File):
    """A pytest `Collector` for jupyter notebooks."""

    def collect(): ...  # noqa: ANN201, D102


def pytest_collect_file(file_path: Path, parent: pytest.Collector) -> NotebookCollector | None:
    """Hook implementation to collect jupyter notebooks."""
    if file_path.suffix == ".ipynb":
        return NotebookCollector.from_parent(parent=parent, path=file_path)
    return None
