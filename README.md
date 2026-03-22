# Agentic Engineer Framework

> I see Agentic Engineering as the modern day LEGO bricks. In a LEGO structure, often times you don't see all the pieces, but they can be integral to the structure. I believe code operates in the same way — the structure can sometimes be dependent on things we may not see. I am not an engineer by trade, but I aim to be one by practice. This framework helps me mitigate my slop code and build in a more elegant fashion.

---

## What This Is

A drop-in observability and quality framework for any Python project. Every function describes itself at runtime — docstrings become live trace logs, nested call chains are fully visible, and AI coding assistants (Claude, Codex, Cursor) are forced into compliance by hooks.

Three layers working together:

1. **The Decorator** (`@observable`) — wraps any function with automatic entry/exit/error tracing
2. **The Agent Contract** (`CLAUDE.md`, `AGENTS.md`, `.cursorrules`) — tells AI assistants the rules
3. **The Hooks** — automatic enforcement that runs after every edit and before every commit

## What It Looks Like

When you run code instrumented with `@observable`, you see the full call graph:

```
→ calculate: "Handles a calculator request and returns the formatted result."  [endpoint, critical]
  → parse_input: "Extracts and casts operation, a, and b from the request payload."  [transform]
  ← parse_input: completed in 0.000s
  → validate_operation: "Validates that the operation is in the supported set."  [transform]
  ← validate_operation: completed in 0.000s
  → compute: "Performs the arithmetic operation on two operands."  [transform]
  ← compute: completed in 0.000s
← calculate: completed in 0.000s
```

Every function narrates itself. The indentation is the call graph — you see depth at a glance. Errors are caught and traced with full context.

---

## Quickstart

### New project — clone the scaffold

```bash
git clone https://github.com/ruffinellimarco/Agentic-Engineer-Framework.git my-project
cd my-project
python -m src.main
```

### Existing project — copy the essentials

```bash
# From the cloned repo, target your existing project
./install.sh ../my-existing-project
```

This copies `contracts/`, `evals/`, `hooks/`, `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, and `.claude/settings.json` into your project.

---

## Project Structure

```
├── .claude/settings.json      # Claude Code hooks (auto-run after Edit/Write)
├── .cursorrules               # Cursor AI rules
├── AGENTS.md                  # Codex / ChatGPT agent contract
├── CLAUDE.md                  # Claude Code agent contract
├── contracts/
│   └── observable.py          # @observable decorator (sync + async)
├── evals/
│   └── check_observability.py # CI compliance checker
├── hooks/
│   ├── post_edit_check.py     # Runs after every file edit
│   └── pre_commit_check.py    # Blocks commits with violations
├── src/                       # Production code (must pass all checks)
├── tests/                     # All tests live here (TDD)
└── scratch/                   # Exploration & prototyping (excluded from evals)
```

---

## How It Works

### The `@observable` Decorator

```python
from contracts.observable import observable

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
```

Works with both sync and async functions. Tags classify the function's role: `endpoint`, `db`, `transform`, `external-api`, `critical`, `billing`, `auth`, `cache`.

### Hooks — Automatic Enforcement

| Trigger | What Runs | What It Catches |
|---|---|---|
| Every `Edit`/`Write` in Claude Code | `hooks/post_edit_check.py` | Missing docstrings, missing `@observable`, broken traces |
| Every `git commit` | `hooks/pre_commit_check.py` | Same — blocks the commit |
| CI push | `evals/check_observability.py` | Full scan with compliance metrics |

Hook output after an edit:
```
── obs-check ──────────────────────────────────────────
✅ 10/10 functions compliant (100%) | 2 endpoint(s) traced

  Endpoint traces:
    → calculate  [endpoint, critical]
      → compute  [transform]
      → parse_input  [transform]
      → validate_operation  [transform]

─────────────────────────────────────────────────────
```

### TDD Workflow

1. **Think** in `scratch/` — explore, prototype, no rules
2. **Test** in `tests/` — write the test first, watch it fail
3. **Build** in `src/` — implement with `@observable` + docstrings, watch it pass
4. **Hooks verify** — compliance checked automatically after every edit

---

## Configuration

```python
from contracts.observable import ObservabilityConfig

ObservabilityConfig.configure(
    emit_to="stdout",           # "stdout" | "cloud_logging" | "custom"
    project_name="my-app",
    include_args=False,         # Log function arguments (watch for PII)
    include_return=False,       # Log return values
    max_depth=20,               # Circuit breaker for deep recursion
)
```

### Custom emitter (Datadog, Sentry, etc.)

```python
def my_emitter(message: str, level: str, meta: dict):
    datadog.send_log(message, level=level, tags=meta.get("tags", []))

ObservabilityConfig.configure(emit_to="custom", custom_emitter=my_emitter)
```

---

## CI Integration

Add to GitHub Actions:

```yaml
- name: Observability compliance check
  run: python -m evals.check_observability ./src ./tests

- name: Run tests
  run: pytest tests/ -v
```

---

## Agent Compatibility

| Agent | Config File | Auto-loaded |
|---|---|---|
| Claude Code | `CLAUDE.md` + `.claude/settings.json` | Yes |
| OpenAI Codex | `AGENTS.md` | Yes |
| Cursor | `.cursorrules` | Yes |
| Others | Copy rules into system prompt | Manual |

---

## License

MIT
