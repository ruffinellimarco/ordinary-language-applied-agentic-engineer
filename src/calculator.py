"""
src/calculator.py
=================
Calculator service — demonstrates full @observable trace chain.
Every function is self-describing at runtime with nested call visibility.
"""

from contracts.observable import observable


SUPPORTED_OPS = {"add", "sub", "mul", "div"}


@observable(tags=["endpoint", "critical"])
def calculate(payload: dict) -> dict:
    """Handles a calculator request and returns the formatted result."""
    try:
        op, a, b = parse_input(payload)
        validate_operation(op)
        result = compute(op, a, b)
        return {"status": "ok", "result": format_result(result)}
    except (ValueError, ZeroDivisionError) as exc:
        return {"status": "error", "error": str(exc)}


@observable(tags=["transform"])
def parse_input(payload: dict) -> tuple:
    """Extracts and casts operation, a, and b from the request payload."""
    try:
        op = payload["operation"]
        a = float(payload["a"])
        b = float(payload["b"])
    except (KeyError, TypeError) as exc:
        raise ValueError(f"Invalid payload: {exc}") from exc
    return op, a, b


@observable(tags=["transform"])
def validate_operation(op: str) -> None:
    """Validates that the operation is in the supported set."""
    if op not in SUPPORTED_OPS:
        raise ValueError(f"Unsupported operation: '{op}'. Supported: {SUPPORTED_OPS}")


@observable(tags=["transform"])
def compute(op: str, a: float, b: float) -> float:
    """Performs the arithmetic operation on two operands."""
    if op == "add":
        return a + b
    elif op == "sub":
        return a - b
    elif op == "mul":
        return a * b
    elif op == "div":
        if b == 0:
            raise ZeroDivisionError("Division by zero")
        return a / b
    raise ValueError(f"Unknown operation: {op}")


def format_result(value: float) -> str:
    """Formats a numeric result to two decimal places."""
    return f"{value:.2f}"
