from pathlib import Path

import pytest

import pytest_ipynb2
import pytest_ipynb2.plugin
from pytest_ipynb2._pytester_helpers import CollectedDir, CollectionTree, ExampleDir


@pytest.fixture
def expected_tree(request: pytest.FixtureRequest, example_dir: CollectedDir) -> CollectionTree:
    trees = {
        "notebook": {
            ("<Session  exitstatus='<UNSET>' testsfailed=0 testscollected=0>", pytest.Session): {
                (f"<Dir {example_dir.pytester_instance.path.name}>", pytest.Dir): {
                    ("<Notebook notebook.ipynb>", pytest_ipynb2.plugin.Notebook): {
                        ("<Cell 4>", pytest_ipynb2.plugin.Cell): {
                            ("<Function test_adder>", pytest.Function): None,
                            ("<Function test_globals>", pytest.Function): None,
                        },
                    },
                },
            },
        },
        "notebook_2tests": {
            ("<Session  exitstatus='<UNSET>' testsfailed=0 testscollected=0>", pytest.Session): {
                (f"<Dir {example_dir.pytester_instance.path.name}>", pytest.Dir): {
                    ("<Notebook notebook_2tests.ipynb>", pytest_ipynb2.plugin.Notebook): {
                        ("<Cell 4>", pytest_ipynb2.plugin.Cell): {
                            ("<Function test_adder>", pytest.Function): None,
                            ("<Function test_globals>", pytest.Function): None,
                        },
                        ("<Cell 6>", pytest_ipynb2.plugin.Cell): {
                            ("<Function test_another_function>", pytest.Function): None,
                        },
                    },
                },
            },
        },
        "both notebooks": {
            ("<Session  exitstatus='<UNSET>' testsfailed=0 testscollected=0>", pytest.Session): {
                (f"<Dir {example_dir.pytester_instance.path.name}>", pytest.Dir): {
                    ("<Notebook notebook.ipynb>", pytest_ipynb2.plugin.Notebook): {
                        ("<Cell 4>", pytest_ipynb2.plugin.Cell): {
                            ("<Function test_adder>", pytest.Function): None,
                            ("<Function test_globals>", pytest.Function): None,
                        },
                    },
                    ("<Notebook notebook_2tests.ipynb>", pytest_ipynb2.plugin.Notebook): {
                        ("<Cell 4>", pytest_ipynb2.plugin.Cell): {
                            ("<Function test_adder>", pytest.Function): None,
                            ("<Function test_globals>", pytest.Function): None,
                        },
                        ("<Cell 6>", pytest_ipynb2.plugin.Cell): {
                            ("<Function test_another_function>", pytest.Function): None,
                        },
                    },
                },
            },
        },
    }
    return CollectionTree.from_dict(trees[request.param])


@pytest.mark.parametrize(
    ["example_dir", "expected_tree"],
    [
        pytest.param(
            ExampleDir(
                files=[Path("tests/assets/notebook.ipynb").absolute()],
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
            ),
            "notebook",
            id="Simple Notebook",
        ),
        pytest.param(
            ExampleDir(
                files=[Path("tests/assets/notebook_2tests.ipynb").absolute()],
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
            ),
            "notebook_2tests",
            id="Notebook 2 tests",
        ),
        pytest.param(
            ExampleDir(
                files=[
                    Path("tests/assets/notebook_2tests.ipynb").absolute(),
                    Path("tests/assets/notebook.ipynb").absolute(),
                ],
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
            ),
            "both notebooks",
            id="Both notebooks - unsorted",
        ),
    ],
    indirect=True,
)
def test_cell_collected(example_dir: CollectedDir, expected_tree: CollectionTree):
    assert CollectionTree.from_items(example_dir.items) == expected_tree


@pytest.mark.parametrize(
    "example_dir",
    [
        pytest.param(
            ExampleDir(
                files=[Path("tests/assets/notebook.ipynb").absolute()],
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
            ),
            id="Simple Notebook",
        ),
    ],
    indirect=True,
)
def test_notebook_collection(example_dir: CollectedDir):
    files = list(example_dir.dir_node.collect())
    assert files
    assert len(files) == 1
    assert files[0].name == "notebook.ipynb"
    assert repr(files[0]) == "<Notebook notebook.ipynb>"


@pytest.mark.parametrize(
    "example_dir",
    [
        pytest.param(
            ExampleDir(
                files=[Path("tests/assets/notebook.ipynb").absolute()],
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
            ),
            id="Simple Notebook",
        ),
    ],
    indirect=True,
)
def test_cell_collection(example_dir: CollectedDir):
    files = list(example_dir.dir_node.collect())
    cells = list(files[0].collect())
    assert cells
    assert len(cells) == 1
    assert cells[0].name == "Cell4"
    assert repr(cells[0]) == "<Cell 4>"


@pytest.mark.parametrize(
    "example_dir",
    [
        pytest.param(
            ExampleDir(
                files=[Path("tests/assets/notebook.ipynb").absolute()],
                conftest="pytest_plugins = ['pytest_ipynb2.plugin']",
            ),
            id="Simple Notebook",
        ),
    ],
    indirect=True,
)
def test_functions(example_dir: CollectedDir):
    files = list(example_dir.dir_node.collect())
    cells = list(files[0].collect())
    functions = list(cells[0].collect())
    assert functions
    assert len(functions) == 2
    assert [f.name for f in functions] == ["test_adder", "test_globals"]
    assert [repr(f) for f in functions] == ["<Function test_adder>", "<Function test_globals>"]
    assert [f.nodeid for f in functions] == ["notebook.ipynb::Cell4::test_adder", "notebook.ipynb::Cell4::test_globals"]
