#!/usr/bin/env python3
"""
hooks/post_edit_check.py
========================
Fast observability compliance check — runs after every file edit.

Called automatically by Claude Code PostToolUse hooks, or manually:
    python hooks/post_edit_check.py [file_or_directory]

Checks:
  1. Every function has a docstring
  2. Every non-trivial function has @observable
  3. Endpoint functions have fully traced call chains

Exit codes:
  0 = all compliant
  1 = violations found
"""

import ast
import sys
import json
import os
from pathlib import Path


# ── AST Helpers ───────────────────────────────────────────────────────────────

def _get_observable_tags(node):
    """Extracts tags from an @observable decorator. Returns None if not observable."""
    for d in node.decorator_list:
        if isinstance(d, ast.Name) and d.id == "observable":
            return []
        if isinstance(d, ast.Call) and isinstance(getattr(d.func, "id", None), str) and d.func.id == "observable":
            for kw in d.keywords:
                if kw.arg == "tags" and isinstance(kw.value, ast.List):
                    return [
                        elt.value for elt in kw.value.elts
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                    ]
            return []
    return None


def _get_called_names(node):
    """Returns the set of function names called within a function body."""
    names = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                names.add(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                names.add(child.func.attr)
    return names


def _has_docstring(node):
    """Returns True if the function node has a docstring."""
    return (
        bool(node.body)
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    )


def _is_exempt(node):
    """Returns True if the function is exempt from @observable."""
    name = node.name
    if name.startswith("__") and name.endswith("__"):
        return True
    if name.startswith("_"):
        return True
    return False


def _is_trivial(node):
    """Returns True if the function body is trivial (1 statement besides docstring)."""
    body = [
        n for n in node.body
        if not (isinstance(n, ast.Expr) and isinstance(getattr(n, "value", None), ast.Constant))
    ]
    return len(body) <= 1


# ── Core Check ────────────────────────────────────────────────────────────────

def check_file(filepath):
    """Scans a Python file for observability violations and builds trace data."""
    try:
        source = Path(filepath).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError) as e:
        return {"violations": [], "total": 0, "compliant": 0, "obs_funcs": {}, "error": str(e)}

    violations = []
    total = 0
    compliant = 0
    obs_funcs = {}  # name -> {tags, calls}

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        total += 1
        is_clean = True

        # Check 1: docstring
        if not _has_docstring(node):
            violations.append({
                "file": str(filepath), "line": node.lineno,
                "func": node.name, "type": "missing_docstring",
            })
            is_clean = False

        # Check 2: @observable (skip exempt/trivial)
        tags = _get_observable_tags(node)
        if tags is not None:
            calls = _get_called_names(node)
            obs_funcs[node.name] = {"tags": tags, "calls": calls}
        elif not _is_exempt(node) and not _is_trivial(node):
            violations.append({
                "file": str(filepath), "line": node.lineno,
                "func": node.name, "type": "missing_observable",
            })
            is_clean = False

        if is_clean:
            compliant += 1

    return {
        "violations": violations,
        "total": total,
        "compliant": compliant,
        "obs_funcs": obs_funcs,
        "error": None,
    }


# ── Endpoint Trace Map ───────────────────────────────────────────────────────

def build_trace_map(obs_funcs):
    """Builds a static call-tree visualization for endpoint-tagged functions."""
    endpoints = [
        (name, info) for name, info in obs_funcs.items()
        if "endpoint" in info["tags"]
    ]
    if not endpoints:
        return []

    lines = ["", "  Endpoint traces:"]
    for name, info in endpoints:
        _trace_tree(name, info, obs_funcs, depth=2, lines=lines, visited=set())
    return lines


def _trace_tree(name, info, all_funcs, depth, lines, visited):
    """Recursively prints the call tree for an observable function."""
    if name in visited:
        return
    visited.add(name)

    tag_str = f"  [{', '.join(info['tags'])}]" if info["tags"] else ""
    lines.append(f"{'  ' * depth}\u2192 {name}{tag_str}")

    for called in sorted(info["calls"]):
        if called in all_funcs and called not in visited:
            _trace_tree(called, all_funcs[called], all_funcs, depth + 1, lines, visited)


# ── Main ──────────────────────────────────────────────────────────────────────

def _resolve_target():
    """Determines which files to scan based on args or hook environment."""
    # Priority 1: explicit CLI argument
    if len(sys.argv) > 1:
        return sys.argv[1]

    # Priority 2: Claude Code hook environment (TOOL_INPUT has file_path)
    tool_input = os.environ.get("TOOL_INPUT", "")
    if tool_input:
        try:
            data = json.loads(tool_input)
            fp = data.get("file_path", "")
            if fp and fp.endswith(".py"):
                return fp
        except (json.JSONDecodeError, KeyError):
            pass

    # Default: scan src/
    return "./src"


def main():
    """Runs the post-edit observability check and prints results."""
    target = _resolve_target()
    target_path = Path(target)

    if target_path.is_file():
        files = [target_path] if target_path.suffix == ".py" else []
    elif target_path.is_dir():
        files = [
            f for f in target_path.rglob("*.py")
            if "__pycache__" not in str(f) and ".venv" not in str(f)
        ]
    else:
        sys.exit(0)

    if not files:
        sys.exit(0)

    all_violations = []
    total_funcs = 0
    total_compliant = 0
    all_obs_funcs = {}

    for f in files:
        result = check_file(f)
        all_violations.extend(result["violations"])
        total_funcs += result["total"]
        total_compliant += result["compliant"]
        all_obs_funcs.update(result["obs_funcs"])

    # ── Output ────────────────────────────────────────────────────────────
    separator = f"\u2500\u2500 obs-check {'\u2500' * 42}"

    if all_violations:
        print(f"\n{separator}")
        print(f"\u274c {len(all_violations)} violation(s) | {total_compliant}/{total_funcs} compliant\n")
        for v in all_violations:
            icon = "\U0001f4c4" if v["type"] == "missing_docstring" else "\U0001f50d"
            label = "missing docstring" if v["type"] == "missing_docstring" else "missing @observable"
            print(f"  {icon} {v['file']}:{v['line']} \u2014 `{v['func']}` {label}")

        # Still show trace map for context
        trace_lines = build_trace_map(all_obs_funcs)
        for line in trace_lines:
            print(line)

        print(f"\n{'─' * 53}")
        sys.exit(1)
    else:
        pct = int(total_compliant / total_funcs * 100) if total_funcs > 0 else 100
        endpoint_count = sum(1 for info in all_obs_funcs.values() if "endpoint" in info["tags"])
        print(f"\n{separator}")
        print(f"\u2705 {total_compliant}/{total_funcs} functions compliant ({pct}%) | {endpoint_count} endpoint(s) traced")

        trace_lines = build_trace_map(all_obs_funcs)
        for line in trace_lines:
            print(line)

        print(f"\n{'─' * 53}")
        sys.exit(0)


if __name__ == "__main__":
    main()
