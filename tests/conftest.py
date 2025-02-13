from dataclasses import dataclass

import pytest

pytest_plugins = ["pytester"]


@dataclass
class CollectedDir:
    """
    The various elements required to test directory collection.

    - `pytester_instance`: pytest.Pytester
    - `dir_node`: pytest.Dir
    - `items`: list[pytest.Item]
    """

    pytester_instance: pytest.Pytester
    dir_node: pytest.Dir
    items: list[pytest.Item]


@pytest.fixture
def example_dir(request: pytest.FixtureRequest, pytester: pytest.Pytester) -> CollectedDir:
    """Parameterised fixture. Requires a list of `Path`s to copy into a pytester instance."""
    pyfiles = {f"test_{example.stem}": example.read_text() for example in request.param if example.suffix == ".py"}
    if pyfiles:
        pytester.makepyfile(**pyfiles)
    notebooks = [f"{example}" for example in request.param if example.suffix == ".ipynb"]
    for notebook in notebooks:
        pytester.copy_example(notebook)
    dir_node = pytester.getpathnode(pytester.path)
    return CollectedDir(
        pytester_instance=pytester,
        dir_node=dir_node,
        items=pytester.genitems([dir_node]),
    )
