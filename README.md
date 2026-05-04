# Agentic Engineer Framework

> I see Agentic Engineering as the modern day LEGO bricks. In a LEGO structure, often times you don't see all the pieces, but they can be integral to the structure. I believe code operates in the same way. The structure can sometimes be dependent on things we may not see. I am not an engineer by trade, but I aim to be one by practice. This framework helps me mitigate my slop code and build in a more elegant fashion.

---

## What This Is

An npm-installable observability and quality framework for AI-assisted development. One command installs slash commands, hooks, and universal agent instructions. Then `/obs:init` scaffolds any project with:

- **`@observable` decorator** — every function narrates itself at runtime
- **Agent contracts** — Claude, Codex, Cursor, and other code-assisting tools share the same compliance rules
- **Behavioral guardrails** — agent instructions reduce overcomplication, hidden assumptions, and broad diffs
- **Automatic hooks** — violations caught after every edit, blocked before every commit
- **Canonical dictionaries** — `function-dictionary.md` and `file-dictionary.md` track what is implemented and where
- **TDD structure** — `tests/`, `scratch/`, and clean `src/`

## Install

```bash
npx ola-obs-contracts
```

That's it. This installs globally into `~/.claude/`. Now every Claude Code session has:

| Command | What It Does |
|---|---|
| `/obs:init` | Scaffold a new project with full observability |
| `/obs:check` | Run compliance check (docstrings + `@observable`) |
| `/obs:trace` | Show endpoint call-tree visualization |
| `/agent` | Universal post-tool-call checkpoint for agents without native hooks |

Plus a PostToolUse hook that auto-checks compliance after every file edit in Claude Code. Other code-assisting tools should run `/agent` after code-writing tool calls, or wire the same command into their post-edit hook system.

### Other install options

```bash
npx ola-obs-contracts --local       # Install into current project only
npx ola-obs-contracts --uninstall   # Clean removal
npx ola-obs-contracts --help        # Usage info
```

---

## Quick Start

```bash
# 1. Install (one time)
npx ola-obs-contracts

# 2. Open Claude Code in any project, then:
/obs:init my-project

# 3. Start coding — hooks or /agent enforce quality automatically
```

---

## Implementation Guide

Use this framework as a traceability contract for the repository, not as a
style-only ruleset. The goal is that a person or agent can ask "what does this
code do, where is it implemented, and how do we know?" and get the same answer
from runtime traces, static checks, and canonical dictionaries.

### 1. Scaffold the repository

Run `/obs:init` in the project root. This creates the observability contract,
agent instructions, enforcement scripts, and canonical dictionaries:

```bash
/obs:init my-project
```

For an existing project, keep the scaffold but migrate code incrementally:

- Put production code under `src/`.
- Put tests under `tests/`.
- Put experiments under `scratch/`.
- Keep `contracts/`, `evals/`, and `hooks/` committed to the repo.

### 2. Instrument meaningful functions

Every function gets a verb-first docstring. Every function that performs I/O,
business logic, data transformation, external calls, or side effects gets
`@observable`.

```python
from contracts.observable import observable

@observable(tags=["endpoint", "critical"])
def handle_request(payload: dict) -> dict:
    """Handles the incoming request and returns the processed response."""
    validated = validate_payload(payload)
    return process_payload(validated)
```

Use tags to make traces scannable:

- `endpoint` for entry points
- `db` for database reads/writes
- `transform` for business logic or data changes
- `external-api` for third-party calls
- `critical`, `billing`, `auth`, `cache` when relevant

### 3. Maintain the canonical dictionaries

Update both dictionaries in the same change as the code:

- `function-dictionary.md` records implemented functions, file paths,
  signatures, purposes, observable tags, callers/callees, tests, and status.
- `file-dictionary.md` records file responsibilities, exports, dependencies,
  known users, tests, observable surface, and status.

These files are verified artifacts, not agent prose. The checker fails in both
directions:

- code has a function missing from `function-dictionary.md`
- `function-dictionary.md` points to a function that does not exist
- code has a file missing from `file-dictionary.md`
- `file-dictionary.md` points to a file that does not exist
- a dictionary references a missing test file

Run:

```bash
python -m evals.check_dictionaries ./src --report
```

### 4. Use `/agent` after code-writing tool calls

Claude Code gets an automatic PostToolUse hook. Other tools should run `/agent`
after edits or wire the same steps into their hook system.

`/agent` enforces the working loop:

1. Think before coding: state assumptions and ask when unclear.
2. Prefer simple, non-speculative changes.
3. Make surgical edits tied to the task.
4. Define verifiable success criteria.
5. Run observability checks.
6. Update dictionaries.
7. Verify dictionaries.
8. Render endpoint traces.

### 5. Verify before finishing

Run these checks locally and in CI:

```bash
python -m evals.check_observability ./src ./tests --report
python -m evals.check_dictionaries ./src --report
python hooks/post_edit_check.py ./src ./tests
pytest tests/ -v
```

A task is not done until:

- observability compliance passes
- dictionary verification passes
- endpoint traces have no unexplained gaps
- tests for changed behavior pass
- the dictionaries reflect the code that actually exists

---

## What It Looks Like

When you run code instrumented with `@observable`, every function narrates itself:

```
-> calculate: "Handles a calculator request..."  [endpoint, critical]
  -> parse_input: "Extracts operation and operands..."  [transform]
  <- parse_input: completed in 0.000s
  -> validate_operation: "Validates the operation..."  [transform]
  <- validate_operation: completed in 0.000s
  -> compute: "Performs the arithmetic operation..."  [transform]
  <- compute: completed in 0.000s
<- calculate: completed in 0.001s
```

The indentation IS the call graph. You see depth, timing, and purpose at a glance.

---

## What `/obs:init` Creates

```
my-project/
  contracts/
    observable.py            @observable decorator (sync + async)
  evals/
    check_observability.py   CI compliance checker
  hooks/
    post_edit_check.py       Runs after every file edit
    pre_commit_check.py      Blocks commits with violations
  function-dictionary.md     Canonical inventory of functions, locations, tags, tests
  file-dictionary.md         Canonical inventory of files, responsibilities, exports
  tests/                     TDD — all tests live here
  scratch/                   Exploration (excluded from evals)
  src/                       Production code (must pass all checks)
  .claude/settings.json      Project-level hooks
  CLAUDE.md                  Claude Code agent contract
  AGENTS.md                  Codex agent contract
  .cursorrules               Cursor rules
  .gitignore
```

## The `@observable` Decorator

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

Works with both sync and async functions. Tags classify the function:

| Tag | When to Use |
|---|---|
| `endpoint` | HTTP/API entry point — full trace required |
| `db` | Database read/write |
| `transform` | Data transformation or business logic |
| `external-api` | Third-party service call |
| `critical` | Business-critical execution path |
| `billing` | Financial data |
| `auth` | Authentication/authorization |
| `cache` | Caching layer |

---

## Hooks — Automatic Enforcement

| Trigger | What Runs | What It Catches |
|---|---|---|
| Every `Edit`/`Write` | PostToolUse hook | Missing docstrings, missing `@observable`, broken traces |
| Every `git commit` | `pre_commit_check.py` | Same — blocks the commit |
| CI push | `check_observability.py` | Full scan with compliance metrics |

Hook output after an edit:
```
-- obs-check --------------------------------------------------
  10/10 functions compliant (100%) | 2 endpoint(s) traced

  Endpoint traces:
    -> calculate  [endpoint, critical]
      -> compute  [transform]
      -> parse_input  [transform]
      -> validate_operation  [transform]
-----------------------------------------------------
```

---

## TDD Workflow

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

```yaml
- name: Observability compliance check
  run: python -m evals.check_observability ./src ./tests

- name: Canonical dictionary check
  run: python -m evals.check_dictionaries ./src --report

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
| Others | `AGENTS.md` + `/agent` checkpoint | Manual or adapter hook |

Any code-assisting tool can comply by following the Implementation Guide and
running `/agent` after code-writing actions when native hooks are unavailable.

---

## Uninstall

```bash
npx ola-obs-contracts --uninstall
```

Cleanly removes commands, hooks, and templates from `~/.claude/`. Project-level files (contracts/, evals/, etc.) are not touched.

---

## License

MIT
