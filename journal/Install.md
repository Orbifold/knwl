## From PyPI

You can install Knwl directly from PyPI using pip:

```bash
pip install knwl
```

or using `uv`:

```bash
uv add knwl
```

## From Github

Clone the project and install it

```bash
git clone https://github.com/Orbifold/knwl.git
cd knwl
pip install -e .
```

This installs the package in editable mode (also called "development mode"). It creates a symbolic link from your Python environment to the current directory (.)
Any changes you make to the source code take effect immediately without reinstalling
The -e flag stands for "editable"

**Why use it:**

Development workflow: Edit code → test immediately (no reinstall needed)
Debugging: Changes to files like `di.py` are instantly available
Testing: Run tests against your latest changes without pip install each time

**What happens:**

- Reads pyproject.toml to get package metadata
- Installs dependencies listed in the project
- Links the package to site-packages instead of copying files

Alternatively, since Knwl uses `uv` as its package manager, you should use:

```bash
uv sync
```

This achieves the same result but uses `uv`'s workflow instead of pip. Note the uv installs dev dependencies by default when using `uv sync`. Things like `pytest` will be installed automatically.

You can install additional groups of dependencies, for instance, to install the `neo4j` and `dev` groups, you can run:

```bash
uv sync --group "neo4j,dev"
```

or to install all optional groups:

```bash
uv sync --all-groups
```

## Dependency Groups

