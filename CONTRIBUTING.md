# CloudCull Development Guide

## Philosophy: TDD-First
We follow a strict Test-Driven Development workflow. **No code is pushed without a passing test.**

## Workflow
1.  **Write a Test**: Create a new test file in `tests/unit/`.
2.  **Red**: Run `pytest` and watch it fail.
3.  **Green**: Implement the minimal code to pass the test.
4.  **Refactor**: Clean up and optimize.

## Running Tests
```bash
# Run all tests
uv run pytest

# Run specific suite
uv run pytest tests/unit/adapters/test_aws.py
```

## Extending CloudCull

### Adding a New Cloud Provider
1.  Create `adapters/newcloud.py`.
2.  Implement `scan()`, `get_metrics()`, and `stop_instance()`.
3.  Add it to `CloudCullRunner` in `main.py`.
4.  **Requirement**: Must support `--simulated` mode.

### Adding a New LLM Provider
1.  Inherit from `BaseLLM` in `llm/base.py`.
2.  Implement `classify_instance()`.
3.  Register in `llm/factory.py`.

## Dashboard Development
The dashboard is a standard Vite + React app.
```bash
cd dashboard
npm install
npm run dev
```
It reads data from `public/report.json`.
