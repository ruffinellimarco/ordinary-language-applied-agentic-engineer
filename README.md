# Agentic Engineer Framework

> I see Agentic Engineering as the modern day LEGO bricks. In a LEGO structure, often times you don't see all the pieces, but they can be integral to the structure. I believe code operates in the same way — the structure can sometimes be dependent on things we may not see. I am not an engineer by trade, but I aim to be one by practice. This framework helps me mitigate my slop code and build in a more elegant fashion.

---

## What This Is

An npm-installable observability and quality framework for AI-assisted development. One command installs slash commands and hooks into Claude Code. Then `/obs:init` scaffolds any project with:

- **`@observable` decorator** — every function narrates itself at runtime
- **Agent contracts** — Claude, Codex, and Cursor are forced into compliance
- **Automatic hooks** — violations caught after every edit, blocked before every commit
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

Plus a PostToolUse hook that auto-checks compliance after every file edit.

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

# 3. Start coding — hooks enforce quality automatically
```

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
  tests/                     TDD — all tests live here
  scratch/                   Exploration (excluded from evals)
  src/                       Production code (must pass all checks)
  .claude/settings.json      Project-level hooks
  CLAUDE.md                  Claude Code agent contract
  AGENTS.md                  Codex agent contract
  .cursorrules               Cursor rules
  .gitignore
```

---

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

## Uninstall

```bash
npx ola-obs-contracts --uninstall
```

Cleanly removes commands, hooks, and templates from `~/.claude/`. Project-level files (contracts/, evals/, etc.) are not touched.

---

## License

MIT
