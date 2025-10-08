# Testing Guide

This project has two categories of tests:

## Test Categories

### Unit Tests
Tests that don't require external LLM services (Ollama, OpenAI, etc.). These run quickly and use mocks where needed.

### LLM Tests  
Tests that require actual LLM integration and make real API calls. These are marked with `@pytest.mark.llm`.

## Running Tests

### Quick Commands

```bash
# Run only unit tests (fast, no LLM required)
python test_runner.py unit

# Run only LLM tests (requires Ollama running)
python test_runner.py llm

# Run all tests
python test_runner.py all

# Fast unit tests with minimal output
python test_runner.py fast

# Unit tests with coverage report
python test_runner.py coverage
```

### Manual pytest Commands

```bash
# Unit tests only
uv run pytest -m "not llm" -v

# LLM tests only (requires Ollama)
uv run pytest -m "llm" -v

# All tests
uv run pytest -v

# With coverage
uv run pytest -m "not llm" --cov=knwl --cov-report=html
```

## CI/CD Testing

- **GitHub Actions**: Automatically runs unit tests on all PRs and pushes
- **LLM Tests**: Only run when:
  - Manually triggered via workflow dispatch
  - Commit message contains `[test-llm]`

## Requirements for LLM Tests

LLM tests require:
1. Ollama installed and running
2. A language model pulled (e.g., `ollama pull llama3.2:1b`)
3. Environment variable `OLLAMA_HOST` (optional, defaults to localhost:11434)

## Adding New Tests

- **Unit tests**: No special markers needed
- **LLM tests**: Add `@pytest.mark.llm` decorator to any test that calls:
  - `knwl.query()`
  - `knwl.create_kg()`  
  - `knwl.input()`
  - Any method that makes LLM API calls