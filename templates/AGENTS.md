# AGENTS.md — Universal Agent Contract
# Required for all code generation by any AI agent (Codex, ChatGPT, Copilot, Cursor, etc.)

## Rules — Non-Negotiable

1. **Every function MUST have a docstring.** Verb-first, plain English, one line.
2. **Every function that performs I/O, business logic, data transformation, or side effects MUST use `@observable`.**
3. Pure utility functions (type coercion, string formatting) MAY skip `@observable` but MUST still have docstrings.
4. Private helpers (`_prefixed`) are exempt from `@observable` but NOT from docstrings.
5. `__dunder__` methods are exempt from `@observable` but NOT from docstrings.
6. **Every repository MUST keep `function-dictionary.md` and `file-dictionary.md` current.**

## Behavioral Rules — Always Active

Reduce common LLM coding mistakes:

1. Think before coding.
   - State assumptions explicitly.
   - If multiple interpretations exist, present them instead of picking silently.
   - If a simpler approach exists, say so and prefer it.
   - If something is unclear, stop, name the confusion, and ask.

2. Prefer simplicity.
   - Add no features beyond what was requested.
   - Add no abstractions for single-use code.
   - Add no flexibility or configurability that was not requested.
   - If 200 lines could be 50, rewrite it.

3. Make surgical changes.
   - Touch only what the task requires.
   - Do not improve adjacent code, comments, or formatting.
   - Match existing style, even if you would choose differently.
   - Mention unrelated dead code instead of deleting it.
   - Remove only imports, variables, or functions made unused by your change.

4. Define verifiable success.
   - Turn tasks into checks that can pass or fail.
   - For bugs, reproduce the bug before fixing it when practical.
   - For refactors, verify behavior before and after.
   - For multi-step work, state a brief plan with verification for each step.

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
- `function-dictionary.md` — Canonical inventory of implemented functions.
- `file-dictionary.md` — Canonical inventory of files, responsibilities, exports, and tests.

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

## Canonical Dictionaries

The dictionaries are the repository's traceable map. Update them in the same
change as the code so future agents can answer what is implemented and where
without re-discovering the whole project.

### `function-dictionary.md`
For every changed production function, record:
- Function name and signature
- File path
- Purpose matching the docstring
- Observable status and tags
- Known callers and callees
- Test coverage
- Status: `implemented`, `planned`, or `deprecated`

### `file-dictionary.md`
For every added, moved, deleted, or materially changed file, record:
- File path
- Primary responsibility
- Exports
- Important dependencies
- Known users
- Test file
- Observable surface
- Status: `active`, `planned`, or `deprecated`

Use `TBD` for unknown relationships. Do not invent call paths, ownership, or
test coverage.

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
python -m evals.check_observability ./src ./tests --report
python -m evals.check_dictionaries ./src --report
```

All functions must pass before the task is complete. This check also runs
automatically via hooks after every file edit.

If your host tool does not run hooks automatically, run `/agent` after each
code-writing tool call. `/agent` is the universal post-tool-call checkpoint:
it verifies decorators, updates dictionaries, and reports trace gaps.

## Hooks — Automatic Enforcement

This project uses hooks that run automatically:

- **PostToolUse hook**: After every file edit, the observability checker runs and
  reports violations immediately. Fix them before moving on.
- **Pre-commit hook**: Blocks git commits that contain violations.
- **CI check**: GitHub Actions runs the full eval on every push.

You will see hook output after your edits. If violations appear, fix them
in your next edit before proceeding with other work.

## Done Criteria

Before finishing any code task:
- Observability check passes.
- Dictionary check passes with no stale or missing entries.
- Endpoint trace map has no unexplained gaps.
- `function-dictionary.md` reflects changed functions.
- `file-dictionary.md` reflects changed files.
- Tests for changed behavior pass.
