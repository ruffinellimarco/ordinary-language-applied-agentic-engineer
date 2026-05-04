---
name: agent
description: Post-tool-call checkpoint for any code-assisting agent. Verifies observability decorators, updates canonical dictionaries, and reports traceability gaps.
argument-hint: "[changed-file-or-directory]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
---

# Agent Post-Tool-Call Checkpoint

Run this after any code-writing tool call when the host tool does not provide an
automatic PostToolUse hook. Treat it as the universal agent checkpoint for OLA
projects.

## Behavioral Rules

Apply these rules before and after every code-writing action:

1. Think before coding.
   - State assumptions explicitly.
   - If multiple interpretations exist, present them instead of picking silently.
   - If a simpler approach exists, say so.
   - If something is unclear, stop, name the confusion, and ask.

2. Prefer simplicity.
   - Add no features beyond what was requested.
   - Add no abstractions for single-use code.
   - Add no flexibility or configurability that was not requested.
   - If the solution is much longer than it needs to be, simplify it.

3. Make surgical changes.
   - Touch only files and lines tied to the task.
   - Match existing style.
   - Do not refactor unrelated code.
   - Remove only unused imports, variables, or functions created by your change.

4. Define verifiable success.
   - Convert the task into checks that can pass or fail.
   - For bugs, reproduce the bug before fixing it when practical.
   - For new behavior, add or update tests when practical.
   - Loop until checks pass or clearly report the blocker.

## Steps

1. Determine the target:
   - If `$ARGUMENTS` is provided, inspect that file or directory.
   - Otherwise, inspect `./src ./tests`.

2. Run the observability check:
   ```bash
   python -m evals.check_observability $TARGET --report
   ```

3. If violations are found:
   - Add missing verb-first docstrings.
   - Add `@observable` to every function that performs I/O, business logic,
     data transformation, external calls, or side effects.
   - Use the most specific tags available.
   - Re-run the check until it passes.

4. Update `function-dictionary.md`:
   - Add or revise every changed production function.
   - Include file path, purpose, observable status, tags, callers/callees when known,
     and test coverage.
   - Mark unknown relationships as `TBD` instead of guessing.

5. Update `file-dictionary.md`:
   - Add or revise every changed source, test, contract, hook, or eval file.
   - Include file purpose, owned exports, important dependencies, tests, and status.

6. Run the trace map:
   ```bash
   python hooks/post_edit_check.py ./src ./tests
   ```

7. Verify dictionaries in both directions:
   ```bash
   python -m evals.check_dictionaries ./src --report
   ```
   This must fail if:
   - A function exists in code but is missing from `function-dictionary.md`.
   - A `function-dictionary.md` entry points to a function that does not exist.
   - A file exists in code but is missing from `file-dictionary.md`.
   - A `file-dictionary.md` entry points to a file that does not exist.
   - A referenced test file does not exist.

8. Report:
   - Compliance rate and violation count.
   - Dictionary entries added or updated.
   - Any remaining trace gaps or unknown relationships.
