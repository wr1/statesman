# Statesman

Statesman is a Python library for managing states in file-system-based workflows, enabling dependency checks, restarts, and partial iterations for expensive computational steps.

## Installation

```bash
pip install statesman
```

Alternatively, using uv:
```bash
uv pip install statesman
```

## Usage

Define workflow steps by subclassing `Statesman` and using Pydantic models for state validation.

The working directory can be specified in the config YAML under the key `workdir` (default) or an alternative key by setting the `workdir_key` class attribute to a dotted path, e.g., `'paths.workdir'` for nested configurations.

See `examples/demo_workflow.py` for a demonstration. To run the demo:
```bash
python examples/demo_workflow.py
```

## Development

- Install dependencies with uv: `uv sync --all-extras`
- Run tests: `uv run pytest`
- Format and check code: `uv run ruff format` and `uv run ruff check --fix`
