# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Consolidated and simplified tests

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
