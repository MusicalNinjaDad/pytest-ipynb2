from pathlib import Path

import pytest
from conftest import CollectedDir

import pytest_ipynb2
from pytest_ipynb2.pytester_helpers import CollectionTree, ExampleDir


@pytest.mark.xfail
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
def test_cell_collected(example_dir: CollectedDir):
    tree_dict = {
        ("<Session  exitstatus='<UNSET>' testsfailed=0 testscollected=0>", pytest.Session): {
            (f"<Dir {example_dir.pytester_instance.path.name}>", pytest.Dir): {
                ("<Notebook notebook.ipynb>", pytest_ipynb2.Notebook): {
                    ("<Cell 4>", pytest_ipynb2.Cell): {
                        ("<Function test_adder>", pytest.Function): None,
                        ("<Function test_globals>", pytest.Function): None,
                    },
                },
            },
        },
    }
    expected_tree = CollectionTree.from_dict(tree_dict)
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
    assert repr(files[0]) == "<NotebookCollector notebook.ipynb>"


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
    assert cells[0].name == "Cell 4"
    assert repr(cells[0]) == "<NotebookCellCollector Cell 4>"


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
