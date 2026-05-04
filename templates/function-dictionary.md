# Function Dictionary

This is the canonical inventory of implemented functions. Keep it current after
every code change so agents can answer "what exists, where is it, and how is it
traced?" without rediscovering the codebase from scratch.

## Maintenance Rules

- Update this file in the same change as the function implementation.
- Include production functions from `src/`, contracts, hooks, and evals.
- Include test helpers only when they are shared or non-obvious.
- Mark unknown callers/callees as `TBD`; do not invent relationships.
- Keep entries concise. Prefer one line per field.
- `python -m evals.check_dictionaries ./src --report` fails when this file is stale or incomplete.

## Entry Template

```md
### `function_name`
- File: `src/module.py`
- Signature: `function_name(arg: Type) -> ReturnType`
- Purpose: Verb-first sentence that matches the function docstring.
- Observable: `yes` | `no`
- Tags: `endpoint`, `transform`, `db`, `external-api`, `critical`, `billing`, `auth`, `cache`
- Called by: `caller_name` | `TBD` | `none`
- Calls: `callee_name` | `TBD` | `none`
- Tests: `tests/test_module.py::TestClass::test_name`
- Status: `implemented` | `planned` | `deprecated`
```

## Functions

<!-- Add function entries here. -->
