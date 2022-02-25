# Linux

### Install poetry

```bash
python3 -m pip install poetry
```

### Install the Python dependencies into a virtual environment managed by Poetry.

```bash
poetry install
```

### Run kasatk

```bash
poetry run kasatk
```

### Check code formatting and linting

This uses the `flake8-black` and `flake8-isort` plugins to also check `black`
and `isort` with just one command.

```bash
poetry run flake8
```
