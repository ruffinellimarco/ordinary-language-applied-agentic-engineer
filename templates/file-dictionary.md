# File Dictionary

This is the canonical inventory of repository files and their responsibilities.
Keep it current after every code change so agents can understand module ownership
and avoid duplicating implemented behavior.

## Maintenance Rules

- Update this file when adding, moving, deleting, or materially changing files.
- Every production file must have a clear responsibility and test pointer.
- Keep file ownership narrow: one file should have one primary concern.
- Mark unclear dependencies or ownership as `TBD`; do not guess.
- `python -m evals.check_dictionaries ./src --report` fails when this file is stale or incomplete.

## Entry Template

```md
### `src/module.py`
- Purpose: One sentence describing the file's responsibility.
- Exports: `function_name`, `ClassName`
- Depends on: `contracts.observable`, `src.other_module`
- Used by: `src.entrypoint`, `tests/test_module.py`
- Tests: `tests/test_module.py`
- Observable surface: `function_name`, `other_function`
- Status: `active` | `planned` | `deprecated`
```

## Files

### `src/__init__.py`
- Purpose: Marks `src/` as the production package root.
- Exports: none
- Depends on: none
- Used by: Project imports
- Tests: `TBD`
- Observable surface: none
- Status: `active`

### `contracts/observable.py`
- Purpose: Provides the `@observable` decorator and runtime tracing configuration.
- Exports: `observable`, `ObservabilityConfig`
- Depends on: Python standard library
- Used by: Production functions that need runtime traces.
- Tests: `tests/test_observable.py`
- Observable surface: none
- Status: `active`

### `evals/check_observability.py`
- Purpose: Scans Python files for missing docstrings and missing `@observable` decorators.
- Exports: CLI module `python -m evals.check_observability`
- Depends on: Python standard library
- Used by: hooks, CI, `/obs:check`, `/agent`
- Tests: `TBD`
- Observable surface: none
- Status: `active`

### `hooks/post_edit_check.py`
- Purpose: Runs the fast post-edit observability check and prints endpoint trace maps.
- Exports: CLI script `python hooks/post_edit_check.py`
- Depends on: `evals/check_observability.py` concepts, Python standard library
- Used by: PostToolUse hooks, `/obs:trace`, `/agent`
- Tests: `TBD`
- Observable surface: none
- Status: `active`

### `evals/check_dictionaries.py`
- Purpose: Verifies that canonical function and file dictionaries match scanned source code.
- Exports: CLI module `python -m evals.check_dictionaries`
- Depends on: Python standard library
- Used by: CI, `/obs:check`, `/agent`
- Tests: `TBD`
- Observable surface: none
- Status: `active`

<!-- Add project-specific file entries here. -->
