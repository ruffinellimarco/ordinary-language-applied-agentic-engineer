"""
evals/check_dictionaries.py
===========================
CI check that verifies canonical dictionaries against the codebase.

Usage:
    python -m evals.check_dictionaries ./src --report

Exit codes:
    0 = dictionaries match scanned code
    1 = missing or stale dictionary entries found
"""

import argparse
import ast
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


ENTRY_RE = re.compile(r"^### `([^`]+)`\s*$")
FIELD_RE = re.compile(r"^- ([^:]+):\s*(.*)\s*$")


@dataclass(frozen=True)
class CodeFunction:
    """Represents a function discovered in source code."""
    name: str
    filepath: str
    line: int

    @property
    def key(self) -> tuple[str, str]:
        """Returns the canonical function lookup key."""
        return (self.filepath, self.name)


@dataclass
class DictionaryEntry:
    """Represents a parsed Markdown dictionary entry."""
    heading: str
    fields: dict[str, str] = field(default_factory=dict)


@dataclass
class DictionaryViolation:
    """Represents a dictionary drift violation."""
    violation_type: str
    subject: str
    detail: str


@dataclass
class DictionaryCheckResult:
    """Aggregates dictionary verification results."""
    functions_scanned: int = 0
    files_scanned: int = 0
    function_entries: int = 0
    file_entries: int = 0
    violations: list[DictionaryViolation] = field(default_factory=list)

    @property
    def violation_count(self) -> int:
        """Returns the number of dictionary violations."""
        return len(self.violations)


def _normalize_path(path: str) -> str:
    """Normalizes a path string for dictionary comparisons."""
    return path.strip().strip("`").replace("\\", "/").lstrip("./")


def _is_empty_init(filepath: Path) -> bool:
    """Returns True when the file is an empty __init__.py placeholder."""
    return filepath.name == "__init__.py" and filepath.read_text(encoding="utf-8").strip() == ""


def _iter_python_files(paths: list[str]) -> list[Path]:
    """Returns Python files under the provided paths, excluding generated noise."""
    files = []
    excludes = ("__pycache__", ".venv", "node_modules", "migrations", "generated", "scratch")

    for raw_path in paths:
        root = Path(raw_path)
        if root.is_file() and root.suffix == ".py":
            files.append(root)
        elif root.is_dir():
            for py_file in root.rglob("*.py"):
                path_str = str(py_file).replace("\\", "/")
                if any(excluded in path_str for excluded in excludes):
                    continue
                if _is_empty_init(py_file):
                    continue
                files.append(py_file)

    return sorted(set(files), key=lambda p: str(p))


def _is_documented_function(node: ast.AST) -> bool:
    """Returns True when a function should appear in the canonical dictionary."""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    if node.name.startswith("__") and node.name.endswith("__"):
        return False
    return True


def scan_code_functions(paths: list[str]) -> tuple[list[CodeFunction], set[str]]:
    """Scans source paths and returns discovered functions and files."""
    functions = []
    files = set()

    for filepath in _iter_python_files(paths):
        normalized_file = _normalize_path(str(filepath))
        files.add(normalized_file)
        try:
            tree = ast.parse(filepath.read_text(encoding="utf-8"), filename=str(filepath))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if _is_documented_function(node):
                functions.append(CodeFunction(node.name, normalized_file, node.lineno))

    return functions, files


def parse_dictionary(path: Path, section_name: str) -> list[DictionaryEntry]:
    """Parses a Markdown dictionary into heading entries and fields."""
    if not path.exists():
        return []

    entries = []
    current = None
    in_inventory = False
    inventory_heading = f"## {section_name}".lower()

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().lower() == inventory_heading:
            in_inventory = True
            current = None
            continue
        if not in_inventory:
            continue

        heading_match = ENTRY_RE.match(line)
        if heading_match:
            current = DictionaryEntry(heading_match.group(1))
            entries.append(current)
            continue

        if current is None:
            continue

        field_match = FIELD_RE.match(line)
        if field_match:
            field_name = field_match.group(1).strip().lower()
            current.fields[field_name] = field_match.group(2).strip()

    return entries


def _function_entry_key(entry: DictionaryEntry) -> tuple[str, str] | None:
    """Returns the canonical key for a function dictionary entry."""
    filepath = entry.fields.get("file")
    if not filepath:
        return None
    return (_normalize_path(filepath), entry.heading.strip())


def _split_refs(value: str) -> list[str]:
    """Splits a dictionary reference field into concrete references."""
    if not value:
        return []
    cleaned = value.strip().strip("`")
    lowered = cleaned.lower()
    if lowered in {"none", "tbd", "n/a", "na"}:
        return []
    return [
        item.strip().strip("`")
        for item in re.split(r",|\|", value)
        if item.strip() and item.strip().lower() not in {"none", "tbd", "n/a", "na"}
    ]


def _test_path(ref: str) -> str:
    """Extracts the file path portion from a test reference."""
    return _normalize_path(ref.split("::", 1)[0])


def _add_missing_function_violations(
    result: DictionaryCheckResult,
    code_functions: list[CodeFunction],
    function_entries: list[DictionaryEntry],
) -> None:
    """Adds violations for code functions missing from the function dictionary."""
    entry_keys = {
        key for key in (_function_entry_key(entry) for entry in function_entries)
        if key is not None
    }

    for function in code_functions:
        if function.key not in entry_keys:
            result.violations.append(DictionaryViolation(
                "missing_function_entry",
                f"{function.filepath}:{function.line}",
                f"`{function.name}` exists in code but is missing from function-dictionary.md",
            ))


def _add_stale_function_violations(
    result: DictionaryCheckResult,
    function_entries: list[DictionaryEntry],
) -> None:
    """Adds violations for function dictionary entries that do not exist in code."""
    checked_files: dict[str, set[str]] = {}

    for entry in function_entries:
        key = _function_entry_key(entry)
        if key is None:
            result.violations.append(DictionaryViolation(
                "invalid_function_entry",
                entry.heading,
                "Function dictionary entry is missing a `File` field",
            ))
            continue
        filepath, function_name = key
        source_path = Path(filepath)
        if not source_path.exists():
            result.violations.append(DictionaryViolation(
                "stale_function_entry",
                f"{filepath}::{function_name}",
                "function-dictionary.md points to a file that does not exist",
            ))
            continue

        if filepath not in checked_files:
            functions, _ = scan_code_functions([filepath])
            checked_files[filepath] = {function.name for function in functions}

        if function_name not in checked_files[filepath]:
            result.violations.append(DictionaryViolation(
                "stale_function_entry",
                f"{filepath}::{function_name}",
                "function-dictionary.md points to a function that does not exist in code",
            ))


def _add_file_violations(
    result: DictionaryCheckResult,
    code_files: set[str],
    file_entries: list[DictionaryEntry],
) -> None:
    """Adds missing and stale file dictionary violations."""
    entry_paths = {_normalize_path(entry.heading) for entry in file_entries}

    for filepath in sorted(code_files):
        if filepath not in entry_paths:
            result.violations.append(DictionaryViolation(
                "missing_file_entry",
                filepath,
                "file exists in code but is missing from file-dictionary.md",
            ))

    for entry_path in sorted(entry_paths):
        if not Path(entry_path).exists():
            result.violations.append(DictionaryViolation(
                "stale_file_entry",
                entry_path,
                "file-dictionary.md points to a file that does not exist",
            ))


def _add_test_reference_violations(
    result: DictionaryCheckResult,
    function_entries: list[DictionaryEntry],
    file_entries: list[DictionaryEntry],
) -> None:
    """Adds violations for test references that point to missing files."""
    for entry in [*function_entries, *file_entries]:
        for ref in _split_refs(entry.fields.get("tests", "")):
            test_file = Path(_test_path(ref))
            if not test_file.exists():
                result.violations.append(DictionaryViolation(
                    "missing_test_reference",
                    f"{entry.heading} -> {ref}",
                    "dictionary test reference points to a missing file",
                ))


def check_dictionaries(paths: list[str]) -> DictionaryCheckResult:
    """Checks function and file dictionaries against scanned source paths."""
    code_functions, code_files = scan_code_functions(paths)
    function_entries = parse_dictionary(Path("function-dictionary.md"), "Functions")
    file_entries = parse_dictionary(Path("file-dictionary.md"), "Files")

    result = DictionaryCheckResult(
        functions_scanned=len(code_functions),
        files_scanned=len(code_files),
        function_entries=len(function_entries),
        file_entries=len(file_entries),
    )

    if not Path("function-dictionary.md").exists():
        result.violations.append(DictionaryViolation(
            "missing_dictionary",
            "function-dictionary.md",
            "canonical function dictionary is missing",
        ))
    if not Path("file-dictionary.md").exists():
        result.violations.append(DictionaryViolation(
            "missing_dictionary",
            "file-dictionary.md",
            "canonical file dictionary is missing",
        ))

    _add_missing_function_violations(result, code_functions, function_entries)
    _add_stale_function_violations(result, function_entries)
    _add_file_violations(result, code_files, file_entries)
    _add_test_reference_violations(result, function_entries, file_entries)

    return result


def _print_report(result: DictionaryCheckResult) -> None:
    """Prints dictionary verification metrics."""
    print(f"\n  Files scanned:        {result.files_scanned}")
    print(f"  Functions scanned:    {result.functions_scanned}")
    print(f"  File entries:         {result.file_entries}")
    print(f"  Function entries:     {result.function_entries}")
    print(f"  Dictionary violations:{result.violation_count}")


def main() -> None:
    """Runs dictionary verification and exits with the correct code."""
    parser = argparse.ArgumentParser(description="Canonical dictionary verifier")
    parser.add_argument("path", nargs="*", default=["./src"], help="Source paths to verify")
    parser.add_argument("--report", action="store_true", help="Print full report even if passing")
    args = parser.parse_args()

    result = check_dictionaries(args.path)

    if result.violations:
        print(f"\n❌  {result.violation_count} dictionary violation(s) found:\n")
        for violation in result.violations:
            print(f"  - {violation.violation_type}: {violation.subject}")
            print(f"    {violation.detail}")
        _print_report(result)
        print()
        sys.exit(1)

    print("\n✅  Canonical dictionaries match scanned code.")
    if args.report:
        _print_report(result)
    print()
    sys.exit(0)


if __name__ == "__main__":
    main()
