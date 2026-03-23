# AGENTS.md — Observability Contract
# Required for all code generation by any AI agent (Codex, ChatGPT, Copilot, etc.)

## Rules — Non-Negotiable

1. **Every function MUST have a docstring.** Verb-first, plain English, one line.
2. **Every function that performs I/O, business logic, data transformation, or side effects MUST use `@observable`.**
3. Pure utility functions (type coercion, string formatting) MAY skip `@observable` but MUST still have docstrings.
4. Private helpers (`_prefixed`) are exempt from `@observable` but NOT from docstrings.
5. `__dunder__` methods are exempt from `@observable` but NOT from docstrings.

## Import

```python
from contracts.observable import observable
```

## Docstring Quality

Write as: **[Verb] [what] [from/to/for where/whom].**

| GOOD | BAD |
|---|---|
| `"Fetches active accounts from BigQuery for the given period."` | `"gets accounts"` |
| `"Calculates net premium retention rate for a cohort."` | `"calculates retention"` |
| `"Sends the renewal reminder email via SendGrid."` | `"email"` |

## Tags — Classify Every @observable Function

Pick all that apply:

| Tag | When to Use |
|---|---|
| `endpoint` | Function exposed via HTTP/API — call chain must be fully traced |
| `db` | Reads or writes a database |
| `transform` | Data transformation or business logic |
| `external-api` | Calls a third-party service |
| `critical` | Business-critical execution path |
| `billing` | Touches financial data |
| `auth` | Authentication or authorization |
| `cache` | Caching layer |

## Endpoint Functions — Full Trace Required

Functions tagged `endpoint` are entry points. Every function they call that performs
work MUST also be `@observable`. This creates a visible nested trace at runtime:

```
→ handle_request: "Handles incoming API call"  [endpoint]
  → validate_payload: "Validates the request payload"  [transform]
  ← validate_payload: completed in 0.001s
  → fetch_data: "Pulls records from BigQuery"  [db]
  ← fetch_data: completed in 0.340s
← handle_request: completed in 0.350s
```

If the trace has gaps (uninstrumented functions in the chain), the hooks will flag it.

## Example

```python
from contracts.observable import observable, ObservabilityConfig

ObservabilityConfig.configure(emit_to="stdout", project_name="my-project")

@observable(tags=["endpoint", "critical"])
def handle_request(payload: dict) -> dict:
    """Handles the main incoming request and orchestrates processing."""
    validated = validate_payload(payload)
    result = process_data(validated)
    return {"status": "ok", "result": result}

@observable(tags=["transform"])
def validate_payload(payload: dict) -> dict:
    """Validates and normalizes the incoming request payload."""
    ...

@observable(tags=["transform"])
def process_data(data: dict) -> list:
    """Processes validated data and returns a list of results."""
    ...
```

## TDD — Test-Driven Development (Non-Negotiable)

### Directory discipline
- `tests/` — ALL tests live here. Never in `src/`.
- `scratch/` — Exploration and prototyping. Never deployed.
- `src/` — Production code. Must pass all checks.

### Workflow
1. Write the test first: `tests/test_<module>.py`
2. Run it, watch it fail: `pytest tests/ -v`
3. Implement the function in `src/` with `@observable` + docstring
4. Run it, watch it pass: `pytest tests/`
5. Refactor, run tests again

### Test naming
```python
# tests/test_main.py
class TestHandleRequest:
    def test_valid_payload_returns_ok(self):
        """Verifies handle_request returns ok for valid input."""
        ...
```

When a scratch exploration proves useful, move it to `src/` with full
observability compliance before considering it done.

## Async Functions

The `@observable` decorator works with both sync and async functions:

```python
@observable(tags=["db"])
async def fetch_accounts(period: str) -> list[dict]:
    """Pulls active accounts from BigQuery for the given period."""
    ...
```

## Verification

After writing ANY code, run:

```bash
python -m evals.check_observability ./src
```

All functions must pass before the task is complete. This check also runs
automatically via hooks after every file edit.

## Hooks — Automatic Enforcement

This project uses hooks that run automatically:

- **PostToolUse hook**: After every file edit, the observability checker runs and
  reports violations immediately. Fix them before moving on.
- **Pre-commit hook**: Blocks git commits that contain violations.
- **CI check**: GitHub Actions runs the full eval on every push.

You will see hook output after your edits. If violations appear, fix them
in your next edit before proceeding with other work.
