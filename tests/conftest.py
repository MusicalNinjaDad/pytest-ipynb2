from typing import Protocol

import pytest

from pytest_ipynb2.pytester_helpers import CollectedDir, ExampleDir

pytest_plugins = ["pytester"]


class ExampleDirRequest(Protocol):
    """Typehint to param passed to example_dir."""

    param: ExampleDir


@pytest.fixture
def example_dir(request: ExampleDirRequest, pytester: pytest.Pytester) -> CollectedDir:
    """Parameterised fixture. Requires a list of `Path`s to copy into a pytester instance."""
    for filetocopy in request.param.files:
        pytester.copy_example(str(filetocopy))
    dir_node = pytester.getpathnode(pytester.path)
    return CollectedDir(
        pytester_instance=pytester,
        dir_node=dir_node,
        items=pytester.genitems([dir_node]),
    )
