# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]

### Fixed

- Integration with vscode Test Explorer [#52][pr-52]

### Changed

- CellPath now uses subscript format `path/to/notebook.ipynb[Celln]` [#52][pr-52]

[pr-52]: https://github.com/MusicalNinjaDad/pytest-ipynb2/pull/52

## [0.4.0] - 2025-03-03

### Fixed

- Handle notebooks not in test rootdir [#45][pr-45]
- Improved handling of lines using IPython magics and calls to ipytest [#46][pr-46]

[pr-46]: https://github.com/MusicalNinjaDad/pytest-ipynb2/pull/46

[pr-45]: https://github.com/MusicalNinjaDad/pytest-ipynb2/pull/45

### Changed

- Only issue warnings from cached ExampleDir on verbosity 3 [#40][pr-40]

[pr-40]: https://github.com/MusicalNinjaDad/pytest-ipynb2/pull/40

## [0.3.0] - 2025-03-01

### Added

- Implemented assertion rewriting [#36][pr-36]

### Fixed

- Provide meaningful reports for failing test cases [#36][pr-36]

### Changed

- Simplified xfail_for interface to take testname as keyword and reason as value [#36][pr-36]
- Consolidated, simplified tests [#29][pr-29] & made them faster [#31][pr-31]

[pr-29]: https://github.com/MusicalNinjaDad/pytest-ipynb2/pull/29
[pr-31]: https://github.com/MusicalNinjaDad/pytest-ipynb2/pull/31
[pr-36]: https://github.com/MusicalNinjaDad/pytest-ipynb2/pull/36

## [0.2.1] - 2025-02-19

### Changed

- Improved documentation
- Explicitly show test helpers are an internal concern
- Tidied up test assets

## [0.2.0] - 2025-02-19

### Added

- Test execution reporting in session log and short summary report: [#21][pr-21] & [#24][pr-24]

### Changed

- `_parser.Notebook` API changed: added `.codecells` and `.testcells`, removed `get_codecells()`, `get_testcells()`, `.contents`

[pr-21]: https://github.com/MusicalNinjaDad/pytest-ipynb2/pull/21
[pr-24]: https://github.com/MusicalNinjaDad/pytest-ipynb2/pull/24

## [0.1.0] - 2025-02-14

### Added  

- Pytest plugin collects jupyter notebooks and cells which use the `%%ipytest` magic
- Published documentation for `CollectionTree`.

## [0.0.2] - 2025-02-12

### Added

- `CollectionTree` to allow for comparison of test collection results provided by `pytester`.

## [0.0.1] - 2025-02-12

### Added

- Initial release of `pytest-ipynb2`.
- Added support for running tests in Jupyter Notebooks.
- Implemented `Notebook` class for parsing notebooks and extracting code and test cells.
- Added GitHub Actions workflows for CI/CD, including linting, testing, type-checking, and publishing.
- Added `justfile` for common development tasks.
- Configured `pyproject.toml` with project metadata, dependencies, and tool configurations.
