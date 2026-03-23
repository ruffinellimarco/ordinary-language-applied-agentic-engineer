---
name: obs:check
description: Run observability compliance check on the current project. Reports missing docstrings, missing @observable, and compliance metrics.
argument-hint: "[path]"
allowed-tools:
  - Bash
  - Read
---

# Observability Compliance Check

Run the observability contract checker on this project.

## Steps

1. Determine the target path:
   - If `$ARGUMENTS` is provided, use it
   - Otherwise, default to `./src ./tests`

2. Run the compliance checker:
   ```bash
   python -m evals.check_observability $TARGET --report
   ```

3. If violations are found:
   - List each violation with file, line, function name, and type
   - For each violation, suggest the specific fix (add docstring or add @observable with appropriate tags)
   - Offer to fix them automatically

4. If all compliant:
   - Show the compliance metrics
   - Run the trace map: `python hooks/post_edit_check.py ./src`
   - Display the endpoint call-tree visualization

5. Always show the compliance rate and total function count.
