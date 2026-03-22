#!/usr/bin/env python3
"""
hooks/pre_commit_check.py
=========================
Git pre-commit hook — blocks commits with observability violations.

Install as a git hook:
    cp hooks/pre_commit_check.py .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit

Or use install.sh which does this automatically.

Exit codes:
  0 = commit allowed
  1 = commit blocked (violations found)
"""

import subprocess
import sys
from pathlib import Path


def _get_staged_python_files():
    """Returns list of staged .py files that will be committed."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True, text=True, check=True,
        )
        return [f for f in result.stdout.strip().split("\n") if f.endswith(".py") and f]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def main():
    """Runs the observability check on staged Python files before commit."""
    staged = _get_staged_python_files()
    if not staged:
        sys.exit(0)

    print(f"\n\u2500\u2500 pre-commit: obs-check on {len(staged)} file(s) \u2500\u2500\n")

    # Import the post_edit checker to reuse its logic
    hook_dir = Path(__file__).parent
    sys.path.insert(0, str(hook_dir))
    from post_edit_check import check_file, build_trace_map

    all_violations = []
    total = 0
    compliant = 0
    all_obs = {}

    for filepath in staged:
        result = check_file(filepath)
        all_violations.extend(result["violations"])
        total += result["total"]
        compliant += result["compliant"]
        all_obs.update(result["obs_funcs"])

    if all_violations:
        print(f"\u274c Commit blocked \u2014 {len(all_violations)} violation(s):\n")
        for v in all_violations:
            icon = "\U0001f4c4" if v["type"] == "missing_docstring" else "\U0001f50d"
            label = "missing docstring" if v["type"] == "missing_docstring" else "missing @observable"
            print(f"  {icon} {v['file']}:{v['line']} \u2014 `{v['func']}` {label}")
        print(f"\nFix violations, then `git add` and commit again.\n")
        sys.exit(1)
    else:
        pct = int(compliant / total * 100) if total > 0 else 100
        print(f"\u2705 {compliant}/{total} functions compliant ({pct}%)")

        trace_lines = build_trace_map(all_obs)
        for line in trace_lines:
            print(line)

        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
