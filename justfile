venv := ".venv"

# list available recipes
list:
  @just --list --justfile {{justfile()}}
  
# remove pre-built python libraries, tool caches, build results
clean:
    rm -rf build
    rm -rf test/assets/build
    rm -rf dist
    rm -rf wheelhouse
    rm -rf .ruff_cache
    rm -rf .pytype
    rm -rf .uv_cache
    rm -rf .pytest_cache
    rm -rf .venv*
    rm -rf pycov
    rm -rf .coverage
    find . -depth -type d -name "__pycache__" -exec rm -rf "{}" \;
    find . -depth -type d -path "*.egg-info" -exec rm -rf "{}" \;
    find . -type f -name "*.egg" -delete
    find . -type f -name "*.so" -delete

clean-logs:
    rm -rf .logs
    mkdir -p .logs
    touch .logs/pytest_ipynb2.log

# clean, remove existing .venvs and rebuild the venvs with uv sync
reset: clean install

# (re-)create a venv and install the project and required dependecies for development & testing
install:
    # upgrade until we have confirmation that dependabot will recognise and process the generated requirements.txt
    uv sync --upgrade
    uv export --no-header --no-default-groups --no-emit-project -o requirements.txt

# lint python with ruff
lint:
  uv run ruff check .

# test python
test:
  uv run pytest

# type-check python
type-check:
  UV_PROJECT_ENVIRONMENT="./.venv-3.12" uv run --python 3.12 pytype

# lint and test python
check:
  @- just lint
  @- just test
  @- just type-check

lint-main:
  uv run ruff check . --config=ruff-main.toml

# format and fix linting errors with ruff
fix:
  - uv run ruff check . --fix
  - uv run ruff format .
  - uv run ruff check . --fix # run again to fix any trailing commas

# format with ruff
format:
  uv run ruff format .

#run coverage analysis on python code
cov:
  uv run pytest --cov --cov-report html:pycov --cov-report term --cov-context=test

# serve python coverage results on localhost:8000 (doesn't run coverage analysis)
show-cov:
  python -m http.server -d ./pycov

# serve python docs on localhost:3000
docs:
  uv run mkdocs serve

# use our versions of vscode extensions 
symlink-vscode:
  rm -rf ~/.vscode-server/extensions/ms-python.python-2025.2.0-linux-x64
  ln -s /workspaces/pytest-ipynb2/.vscode-server/extensions/ms-python.python-2025.2.0-linux-x64 \
      ~/.vscode-server/extensions/ms-python.python-2025.2.0-linux-x64