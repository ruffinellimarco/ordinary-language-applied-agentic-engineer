"""
evals/check_observability.py
=============================
CI check — scans the codebase and flags functions that violate the observability contract.

Usage:
    python -m evals.check_observability ./src
    python -m evals.check_observability ./src --strict   # fail on missing docstrings only
    python -m evals.check_observability ./src --report   # print full summary even if passing

Exit codes:
    0 = all functions conform
    1 = violations found
"""

import ast
import sys
import argparse
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class Violation:
    """Represents a single observability contract violation."""
    filepath: str
    line: int
    function_name: str
    violation_type: str   # "missing_docstring" | "missing_observable"


@dataclass
class ScanResult:
    """Aggregated result of scanning a set of files."""
    total_functions: int = 0
    compliant: int = 0
    files_scanned: int = 0
    violations: list = field(default_factory=list)

    @property
    def violation_count(self) -> int:
        """Returns the total number of violations found."""
        return len(self.violations)

    @property
    def compliance_rate(self) -> float:
        """Calculates the percentage of functions that are compliant."""
        if self.total_functions == 0:
            return 1.0
        return self.compliant / self.total_functions


def _has_docstring(node: ast.FunctionDef) -> bool:
    """Returns True if the function node has a docstring."""
    return (
        bool(node.body)
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    )


def _has_observable(node: ast.FunctionDef) -> bool:
    """Returns True if the function has an @observable decorator."""
    for d in node.decorator_list:
        if isinstance(d, ast.Name) and d.id == "observable":
            return True
        if isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == "observable":
            return True
        if isinstance(d, ast.Attribute) and d.attr == "observable":
            return True
    return False


def _is_trivial(node: ast.FunctionDef) -> bool:
    """
    Returns True for functions exempt from @observable requirement:
    - Private/internal helpers (prefixed with _)
    - Very short functions (1-2 statements, likely pure utilities)
    - __dunder__ methods
    """
    name = node.name
    if name.startswith("__") and name.endswith("__"):
        return True
    if name.startswith("_"):
        return True
    non_docstring_body = [
        n for n in node.body
        if not (isinstance(n, ast.Expr) and isinstance(getattr(n, "value", None), ast.Constant))
    ]
    if len(non_docstring_body) <= 1:
        return True
    return False


def _is_test_file(filepath: Path) -> bool:
    """Returns True if the file is in a tests directory or is a test file."""
    path_str = str(filepath).replace("\\", "/")
    return "/tests/" in path_str or path_str.startswith("tests/") or filepath.name.startswith("test_")


def scan_file(filepath: Path) -> tuple[list[Violation], int, int]:
    """Scans a single Python file and returns (violations, total_functions, compliant_count)."""
    violations = []
    total = 0
    compliant = 0
    is_test = _is_test_file(filepath)

    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"  [SKIP] {filepath}: {e}")
        return violations, 0, 0

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        total += 1
        is_clean = True

        if not _has_docstring(node):
            violations.append(Violation(
                filepath=str(filepath),
                line=node.lineno,
                function_name=node.name,
                violation_type="missing_docstring",
            ))
            is_clean = False

        # Test files: enforce docstrings only, skip @observable requirement
        if not is_test and not _is_trivial(node) and not _has_observable(node):
            violations.append(Violation(
                filepath=str(filepath),
                line=node.lineno,
                function_name=node.name,
                violation_type="missing_observable",
            ))
            is_clean = False

        if is_clean:
            compliant += 1

    return violations, total, compliant


def scan_directory(root: Path, exclude: list[str] = None) -> ScanResult:
    """Scans all Python files under root for observability violations."""
    exclude = exclude or ["__pycache__", ".venv", "node_modules", "migrations", "generated", "scratch"]
    result = ScanResult()

    for py_file in root.rglob("*.py"):
        if any(ex in str(py_file) for ex in exclude):
            continue
        file_violations, file_total, file_compliant = scan_file(py_file)
        result.violations.extend(file_violations)
        result.total_functions += file_total
        result.compliant += file_compliant
        result.files_scanned += 1

    return result


def _print_report(result: ScanResult):
    """Prints the full compliance report with metrics."""
    pct = result.compliance_rate * 100
    print(f"\n  Files scanned:   {result.files_scanned}")
    print(f"  Total functions: {result.total_functions}")
    print(f"  Compliant:       {result.compliant}")
    print(f"  Violations:      {result.violation_count}")
    print(f"  Compliance rate: {pct:.0f}%")


def main():
    """Runs the observability compliance check and exits with appropriate code."""
    parser = argparse.ArgumentParser(description="Observability contract compliance checker")
    parser.add_argument("path", nargs="*", default=["."], help="Directories to scan (default: .)")
    parser.add_argument("--strict", action="store_true", help="Only flag missing docstrings")
    parser.add_argument("--report", action="store_true", help="Print full report even if passing")
    args = parser.parse_args()

    combined = ScanResult()
    for p in args.path:
        root = Path(p)
        if root.is_file():
            file_violations, file_total, file_compliant = scan_file(root)
            combined.violations.extend(file_violations)
            combined.total_functions += file_total
            combined.compliant += file_compliant
            combined.files_scanned += 1
        elif root.is_dir():
            result = scan_directory(root)
            combined.violations.extend(result.violations)
            combined.total_functions += result.total_functions
            combined.compliant += result.compliant
            combined.files_scanned += result.files_scanned

    active_violations = [
        v for v in combined.violations
        if not (args.strict and v.violation_type == "missing_observable")
    ]

    if active_violations:
        print(f"\n\u274c  {len(active_violations)} observability violation(s) found:\n")
        for v in active_violations:
            icon = "\U0001f4c4" if v.violation_type == "missing_docstring" else "\U0001f50d"
            label = "missing docstring" if v.violation_type == "missing_docstring" else "missing @observable"
            print(f"  {icon}  {v.filepath}:{v.line} \u2014 `{v.function_name}` \u2014 {label}")

        _print_report(combined)
        print(f"\nRun `python -m evals.check_observability --help` for options.\n")
        sys.exit(1)
    else:
        print(f"\n\u2705  All functions conform to the observability contract.")
        if args.report:
            _print_report(combined)
        else:
            pct = combined.compliance_rate * 100
            print(f"    {combined.compliant}/{combined.total_functions} compliant ({pct:.0f}%) across {combined.files_scanned} file(s)")
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
