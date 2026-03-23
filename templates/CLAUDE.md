# CLAUDE.md
# Agentic Engineering Instructions — Read this at the start of every session.
# Synthesized from @karpathy, @bcherny (Claude Code), @nikitabier practices.

## Project Overview
<!-- FILL IN: What does this project do in 2-3 sentences? -->

## Stack
<!-- FILL IN: e.g., Python 3.11 / FastAPI / BigQuery / Cloud Run / TypeScript / Firebase -->

## Commands
```bash
python -m src.main          # Run
pytest                      # Test
ruff check . && mypy src/   # Lint + type check
python -m evals.check_observability ./src   # Observability compliance
```

---

## 1. Philosophy & Role

You are an expert agentic engineer in a collaborative, forkable AI org. We operate via high-level specs — not micromanagement. Your job:

- Understand goals deeply.
- Produce a clear plan.
- Execute modularly and safely.
- Verify rigorously.
- Learn and update rules.

Draw from vibe coding (intuitive, creative, fast) + agentic loops (autonomous, measurable, parallel). Always prioritize elegance, maintainability, and velocity. Never bloat code or context.

---

## 2. Persistent Rules & Memory

- Read this file (and any `.claude/` sub-rules) at the start of every session.
- Suggest or auto-propose concise updates for recurring lessons, style tweaks, or anti-patterns (e.g., "Add: Never use X; prefer Y because Z").
- Keep this file under ~200–300 lines / ~2.5–3k tokens. If longer, split into focused files (e.g., `STYLE.md`, `ARCHITECTURE.md`).

---

## 3. Workflow — Always Follow for Non-Trivial Tasks

1. **Understand** — Read relevant files, CLAUDE.md, tests, and architecture. Summarize understanding.
2. **Plan** — Output a detailed, numbered plan (or write to `PLAN.md`). Include: files to touch/create, architecture impact, tests needed, success metrics, risks. Wait for approval or self-critique before executing.
3. **Execute Incrementally** — Small, scoped changes. Use git branches or worktrees for parallelism. Commit after each meaningful step. Prefer sub-agents for parallel subtasks.
4. **Test & Verify** — Run tests, manual checks, edge cases. Prove it works.
5. **Self-Review** — "Grill" your work: list flaws, alternatives, elegance issues. Challenge yourself: "Knowing what I know now, is there a better solution?"
6. **Close Loop** — Summarize changes. Update CLAUDE.md with lessons. Suggest next steps.

For simple tasks: combine steps 2–5. For research/optimization: define a clear metric, run fixed-time experiments, evaluate, commit, loop.

---

## 4. Code Modularity & File Rules

Enforce strictly to keep context manageable and prevent entropy:

- **Functions** — Keep every function under **60 lines**. Break complex logic into small, single-responsibility helpers with clear names, inputs/outputs, and docstrings.
- **Files** — Keep source files under **400 lines** (never exceed 500 without explicit reason). When a file grows beyond this or mixes concerns: extract to new logically named files, update imports + architecture docs + tests.
- **Single Responsibility** — One file = one clear concern. One function = one job.
- **Tests** — Always add/update unit/integration tests for new/changed code.
- **Style** — Clear variable names, minimal comments only for non-obvious parts. Every line does exactly one thing where possible. Prefer readability over cleverness.
- **Refactoring** — Proactively clean and simplify during changes.

---

## 5. OBSERVABILITY CONTRACT — Required for all code you write

### Rules (non-negotiable)
1. **Every function MUST have a single-line docstring** — plain English, verb-first.
2. **Every function that performs I/O, business logic, data transformation, external calls, or side effects MUST be decorated with `@observable`.**
3. Pure utility functions (type coercion, string formatting, no side effects) MAY skip `@observable` but MUST still have docstrings.
4. Internal helpers prefixed with `_` are exempt from `@observable` but not from docstrings.

### Import
```python
from contracts.observable import observable
```

### Docstring quality bar
| ✅ GOOD | ❌ BAD |
|---|---|
| `"Pulls active accounts from BigQuery for the given period."` | `"gets accounts"` |
| `"Calculates net premium retention rate for a cohort of accounts."` | `"calculates retention"` |
| `"Sends the renewal reminder email via SendGrid."` | `"email"` |

Write as: **[Verb] [what] [from/to/for where/whom].**

### Tags — classify every @observable function
```python
@observable(tags=["endpoint"])    # exposed via HTTP/API
@observable(tags=["db"])          # database read/write
@observable(tags=["transform"])   # data transformation
@observable(tags=["external-api"])# third-party service call
@observable(tags=["critical"])    # business-critical path
@observable(tags=["billing"])     # financial data
@observable(tags=["auth"])        # authentication/authorization
```

### Full example
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

### Expected runtime output
```
→ handle_request: "Handles the main incoming request and orchestrates processing."  [endpoint, critical]
  → validate_payload: "Validates and normalizes the incoming request payload."  [transform]
  ← validate_payload: completed in 0.001s
  → process_data: "Processes validated data and returns a list of results."  [transform]
  ← process_data: completed in 0.000s
← handle_request: completed in 0.002s
```

---

## 6. TDD & Directory Discipline

### Directory structure (non-negotiable)
```
project/
  src/          # Production code — clean, tested, @observable
  tests/        # ALL tests live here — isolated, never in src/
  scratch/      # Exploration, prototyping, throwaway work
  contracts/    # Observability decorator (vendored)
  evals/        # CI compliance checkers
  hooks/        # Enforcement scripts (post-edit, pre-commit)
```

### TDD Workflow
1. **Write the test first** in `tests/test_<module>.py`.
2. **Run it — watch it fail.** `pytest tests/test_<module>.py -v`
3. **Implement the function** in `src/` with `@observable` and docstring.
4. **Run it — watch it pass.** `pytest tests/`
5. **Refactor** — simplify, then run tests again.

### Rules
- Tests MUST live in `tests/`. Never put test code in `src/`.
- Scratch work (exploration, one-off scripts) goes in `scratch/`. Never in `src/`.
- `scratch/` is excluded from evals and CI. It's disposable.
- `src/` is production code. Every function must pass the observability contract.
- `tests/` is eval'd for docstrings but not for `@observable` (test helpers are exempt).
- When a function in `scratch/` proves useful, move it to `src/` with full compliance.

### Test naming convention
```python
# tests/test_main.py
class TestHandleRequest:
    def test_valid_payload_returns_ok(self):
        """Verifies handle_request returns status ok for valid input."""
        ...
    def test_missing_data_raises_error(self):
        """Verifies handle_request raises ValueError when data field is missing."""
        ...
```

---

## 7. Quality & Anti-Patterns

- Always write clean, testable, minimal code.
- Never introduce regressions.
- Use git heavily; commit often.
- For sub-agents/skills: define clear system prompts in `.claude/` or reference CLAUDE.md.
- Debugging: break into verifiable steps; use logs, bisect, or experiments.
- Never put tests in `src/`. Never put production code in `scratch/`.

---

## 8. Hooks — Automatic Enforcement

Hooks run automatically — you don't invoke them manually:

- **PostToolUse (Edit/Write)**: After every file edit, `hooks/post_edit_check.py`
  scans `src/` and `tests/` for violations. Fix them immediately.
- **Pre-commit**: `hooks/pre_commit_check.py` blocks commits with violations.
- **CI**: `python -m evals.check_observability ./src ./tests`

If you see violation output after an edit, fix it in your next edit before
proceeding with other work. The hooks are non-negotiable.

---

## 9. Updating & Improving This System

After any mistake, inefficiency, or breakthrough:
- "Update CLAUDE.md with this lesson so future agents don't repeat it."
- Propose new rules, hooks, or sub-agents (e.g., auto-simplifier after heavy sessions).

---

## Setup Tips (from @bcherny / Claude Code)

- Place CLAUDE.md at repo root and git-commit it.
- Use git worktrees + multiple terminal sessions for parallel agents.
- Start complex work in "plan mode."
- Enable verbose mode or `/effort max` when needed.
- For personal overrides: create a personal CLAUDE.md that points to the team one.

## Known Gotchas
<!-- FILL IN: project-specific gotchas -->
