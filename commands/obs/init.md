---
name: obs:init
description: Initialize observability contracts in the current project. Creates contracts/, evals/, hooks/, tests/, scratch/ with full @observable enforcement and TDD structure.
argument-hint: "[project-name]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - AskUserQuestion
---

# Initialize Observability Contracts

You are scaffolding a project with the OLA observability framework. Follow these steps exactly.

## Step 1: Check Prerequisites

1. Verify Python is available: run `python --version` or `python3 --version`
2. Check if `contracts/` already exists in the current directory. If it does, ask the user if they want to overwrite.

## Step 2: Read Templates

Read ALL template files from `~/.claude/obs-templates/`. These are the source files to copy into the project:

- `~/.claude/obs-templates/contracts/observable.py`
- `~/.claude/obs-templates/contracts/__init__.py`
- `~/.claude/obs-templates/evals/check_observability.py`
- `~/.claude/obs-templates/evals/__init__.py`
- `~/.claude/obs-templates/hooks/post_edit_check.py`
- `~/.claude/obs-templates/hooks/pre_commit_check.py`
- `~/.claude/obs-templates/tests/__init__.py`
- `~/.claude/obs-templates/tests/test_observable.py`
- `~/.claude/obs-templates/scratch/__init__.py`
- `~/.claude/obs-templates/src/__init__.py`
- `~/.claude/obs-templates/CLAUDE.md`
- `~/.claude/obs-templates/AGENTS.md`
- `~/.claude/obs-templates/dot-cursorrules`
- `~/.claude/obs-templates/dot-gitignore`
- `~/.claude/obs-templates/dot-claude/settings.json`

## Step 3: Create Project Files

Write each template to the corresponding location in the current project:

| Template | Destination |
|---|---|
| `contracts/observable.py` | `contracts/observable.py` |
| `contracts/__init__.py` | `contracts/__init__.py` |
| `evals/check_observability.py` | `evals/check_observability.py` |
| `evals/__init__.py` | `evals/__init__.py` |
| `hooks/post_edit_check.py` | `hooks/post_edit_check.py` |
| `hooks/pre_commit_check.py` | `hooks/pre_commit_check.py` |
| `tests/__init__.py` | `tests/__init__.py` |
| `tests/test_observable.py` | `tests/test_observable.py` |
| `scratch/__init__.py` | `scratch/__init__.py` |
| `src/__init__.py` | `src/__init__.py` |
| `CLAUDE.md` | `CLAUDE.md` |
| `AGENTS.md` | `AGENTS.md` |
| `dot-cursorrules` | `.cursorrules` |
| `dot-gitignore` | `.gitignore` |
| `dot-claude/settings.json` | `.claude/settings.json` |

## Step 4: Customize

If the user provided a `$ARGUMENTS` (project name):
- Replace `<!-- FILL IN: What does this project do in 2-3 sentences? -->` in CLAUDE.md with the project name
- Update `project_name="my-project"` references with the actual name

## Step 5: Verify

Run: `python -m evals.check_observability ./src ./tests --report`

This should show 0 violations and 100% compliance on the empty scaffold.

## Step 6: Summary

Print a summary of what was created:

```
Observability contracts initialized!

Created:
  contracts/    @observable decorator (sync + async)
  evals/        CI compliance checker
  hooks/        Post-edit + pre-commit enforcement
  tests/        TDD test directory
  scratch/      Exploration (excluded from evals)
  src/           Production code directory
  CLAUDE.md     Claude Code agent contract
  AGENTS.md     Codex agent contract
  .cursorrules  Cursor rules
  .gitignore    Python gitignore

Next steps:
  1. Write tests first in tests/
  2. Implement in src/ with @observable + docstrings
  3. Hooks enforce compliance automatically after every edit
```
