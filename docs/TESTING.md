# Testing Guide

This project uses pytest with custom markers to separate different types of tests.

## Test Categories

### Unit Tests
- **Files**: `test_utils.py`, `test_tokenize.py`, `test_cache.py`, `test_entities.py`, etc.
- **Purpose**: Test individual functions and components in isolation
- **Dependencies**: No external services required
- **Run in CI**: ✅ Always run in GitHub Actions

### LLM Integration Tests  
- **Files**: `test_knwl.py` (entire file), individual tests marked with `@pytest.mark.llm`
- **Purpose**: Test functionality that requires LLM/Ollama integration
- **Dependencies**: Requires running Ollama server with models
- **Run in CI**: ❌ Skipped in PyPI publishing workflows

## Running Tests

### Run all tests (requires Ollama):
```bash
uv run pytest
```

### Run only unit tests (no LLM required):
```bash
uv run pytest -m "not llm"
```

### Run only LLM tests (requires Ollama):
```bash
uv run pytest -m "llm"
```

### Run specific test files:
```bash
# Unit tests only
uv run pytest tests/test_utils.py tests/test_tokenize.py

# LLM tests (requires Ollama)
uv run pytest tests/test_knwl.py
```

## CI/CD Behavior

### PyPI Publishing Workflows
- **Command**: `uv run pytest -m "not llm" --cov=knwl --cov-report=xml`
- **Runs**: Only unit tests that don't require external services
- **Skips**: All tests in `test_knwl.py` and any tests marked with `@pytest.mark.llm`

### Optional LLM Testing Workflow
- **Trigger**: Manual dispatch or commit messages containing `[test-llm]`
- **Command**: `uv run pytest -m "llm"`
- **Setup**: Installs and configures Ollama with a small model
- **Runs**: Only LLM-dependent tests

## Adding New Tests

### For unit tests:
- Add to existing test files or create new `test_*.py` files
- No special markers needed
- Will automatically run in CI

### For LLM-dependent tests:
- Add `@pytest.mark.llm` decorator to individual test functions
- Or add entire files to LLM testing by adding `pytestmark = pytest.mark.llm` at module level
- Will be skipped in PyPI workflows but can be run manually or in LLM workflow

## Pytest Configuration

The project uses `pytest.ini` with these key settings:
- **Strict markers**: Prevents typos in marker names
- **LLM marker**: `llm` - marks tests requiring LLM integration  
- **Test discovery**: Automatically finds tests in `tests/` directory