# pytest-ipynb2

A pytest plugin to run tests in Jupyter Notebooks.

Designed to play nicely with [chmp/ipytest](https://github.com/chmp/ipytest).

## Why?

My use case is so that I can teach my son to code and use notebooks to do that but still have the tests show up in vscode test explorer.

We also like to have all our tests run in a github workflow - and this makes that simple too.

## Usage

Usage is very simple:

1. Install from pypi (e.g. with pip):

    ```sh
    pip install pytest-ipynb2
    ```

1. That's it! pytest will now collect and execute any tests in jupyter notebooks when run from the command line or IDE.

1. If you want to run a specific test you can pass it on the command line in the format `pytest path/to/notebook.ipynb[Cell3]::test_name`

## Test identification

I'm assuming you also want to run your tests inside your notebooks ... so simply use the `%%ipytest` magic in a cell and pytest will collect any tests based on the usual naming and identification rules.

> **Note:** tests will *only* be identified in cells which use the `%%ipytest` magic

## Documentation

For more details see the [docs](https://musicalninjadad.github.io/pytest-ipynb2)

## Features

- Enables pytest to collect and execute tests stored within jupyter notebooks
- Provides meaningful test logs identifying the notebook, cell and test function
- Handles tests with fixtures and parametrization
- Executes *all cells above* the test cell before running the tests in that cell.

    >WARNING: this means that if any previous cells have side-effects they will occur on test collection, just as they would if included in a pytest test module.

## Known limitations & To-Dos

This is an early version. The following things are still on my to-do list:

- Handling tests grouped into classes [#22](https://github.com/MusicalNinjaDad/pytest-ipynb2/issues/22) (might work - I've not checked yet)
- v1.0.0 will include dedicated commandline options rather than requiring you to specify the plugin [#12](https://github.com/MusicalNinjaDad/pytest-ipynb2/issues/12)
