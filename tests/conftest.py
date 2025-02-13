import pytest

from pytest_ipynb2.pytester_helpers import CollectedDir

pytest_plugins = ["pytester"]


@pytest.fixture
def example_dir(request: pytest.FixtureRequest, pytester: pytest.Pytester) -> CollectedDir:
    """Parameterised fixture. Requires a list of `Path`s to copy into a pytester instance."""
    for filetocopy in request.param:
        pytester.copy_example(str(filetocopy))
    dir_node = pytester.getpathnode(pytester.path)
    return CollectedDir(
        pytester_instance=pytester,
        dir_node=dir_node,
        items=pytester.genitems([dir_node]),
    )
