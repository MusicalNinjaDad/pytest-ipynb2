# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added  

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
