"""
tests/test_calculator.py
========================
TDD tests for the calculator service.
Written BEFORE the implementation — these should fail first, then pass.
Run with: pytest tests/test_calculator.py -v
"""

import pytest
from src.calculator import calculate, parse_input, validate_operation, compute, format_result


class TestCalculateEndpoint:
    """Tests for the top-level calculate endpoint."""

    def test_add_returns_correct_result(self):
        """Verifies calculate returns the sum for add operation."""
        result = calculate({"operation": "add", "a": 10, "b": 5})
        assert result == {"status": "ok", "result": "15.00"}

    def test_subtract_returns_correct_result(self):
        """Verifies calculate returns the difference for sub operation."""
        result = calculate({"operation": "sub", "a": 10, "b": 3})
        assert result == {"status": "ok", "result": "7.00"}

    def test_multiply_returns_correct_result(self):
        """Verifies calculate returns the product for mul operation."""
        result = calculate({"operation": "mul", "a": 4, "b": 7})
        assert result == {"status": "ok", "result": "28.00"}

    def test_divide_returns_correct_result(self):
        """Verifies calculate returns the quotient for div operation."""
        result = calculate({"operation": "div", "a": 20, "b": 4})
        assert result == {"status": "ok", "result": "5.00"}

    def test_divide_by_zero_returns_error(self):
        """Verifies calculate returns error for division by zero."""
        result = calculate({"operation": "div", "a": 10, "b": 0})
        assert result["status"] == "error"

    def test_invalid_operation_returns_error(self):
        """Verifies calculate returns error for unknown operations."""
        result = calculate({"operation": "pow", "a": 2, "b": 3})
        assert result["status"] == "error"


class TestParseInput:
    """Tests for input parsing."""

    def test_extracts_fields(self):
        """Verifies parse_input extracts operation, a, and b from payload."""
        op, a, b = parse_input({"operation": "add", "a": 1, "b": 2})
        assert op == "add"
        assert a == 1.0
        assert b == 2.0

    def test_missing_field_raises(self):
        """Verifies parse_input raises ValueError for incomplete payloads."""
        with pytest.raises(ValueError):
            parse_input({"operation": "add", "a": 1})


class TestValidateOperation:
    """Tests for operation validation."""

    def test_valid_operations_pass(self):
        """Verifies all supported operations are accepted."""
        for op in ("add", "sub", "mul", "div"):
            validate_operation(op)  # should not raise

    def test_invalid_operation_raises(self):
        """Verifies unsupported operations raise ValueError."""
        with pytest.raises(ValueError):
            validate_operation("pow")


class TestCompute:
    """Tests for the compute function."""

    def test_add(self):
        """Verifies compute performs addition correctly."""
        assert compute("add", 3, 4) == 7.0

    def test_div_by_zero_raises(self):
        """Verifies compute raises ZeroDivisionError for division by zero."""
        with pytest.raises(ZeroDivisionError):
            compute("div", 1, 0)


class TestFormatResult:
    """Tests for result formatting."""

    def test_formats_to_two_decimals(self):
        """Verifies format_result returns a string with two decimal places."""
        assert format_result(3.14159) == "3.14"

    def test_formats_integer(self):
        """Verifies format_result formats whole numbers with .00."""
        assert format_result(42) == "42.00"
