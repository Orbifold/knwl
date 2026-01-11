
You can install Knwl CLI via [pipx](https://github.com/pypa/pipx):
```
git clone https://github.com/Orbifold/knwl.git
cd knwl
python -m pip install --upgrade pipx
python -m pipx install .
```
It keeps the CLI isolated from system Python packages and uses its own virtual environment.

## Info

You can get help and list the available commands by running:
```bash
knwl --help
```
or simply `knwl`.

Via the `info` command, you can get information about your Knwl installation, including version, storage backend, and other environment details:

```bash
knwl info
```