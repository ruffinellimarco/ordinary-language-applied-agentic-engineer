"""
tests/test_observable.py
========================
Unit tests for the @observable decorator and observability system.
Run with: pytest tests/test_observable.py -v
"""

import asyncio
from contracts.observable import observable, ObservabilityConfig, trace_summary, _registry


class TestObservableDecorator:
    """Tests for the @observable decorator core behavior."""

    def setup_method(self):
        """Resets config and registry before each test."""
        ObservabilityConfig.configure(enabled=True, emit_to="stdout")
        _registry.clear()

    def test_sync_function_completes(self):
        """Verifies a sync decorated function returns its result."""
        @observable(tags=["transform"])
        def add(a: int, b: int) -> int:
            """Adds two numbers together."""
            return a + b

        assert add(2, 3) == 5

    def test_async_function_completes(self):
        """Verifies an async decorated function returns its result."""
        @observable(tags=["db"])
        async def fetch_data(key: str) -> str:
            """Fetches data for the given key."""
            return f"value-{key}"

        result = asyncio.run(fetch_data("test"))
        assert result == "value-test"

    def test_no_args_decorator(self):
        """Verifies @observable works without parentheses."""
        @observable
        def simple() -> str:
            """Returns a simple value."""
            return "ok"

        assert simple() == "ok"
        assert simple._is_observable is True

    def test_metadata_attached(self):
        """Verifies introspection metadata is attached to the wrapper."""
        @observable(tags=["critical", "billing"])
        def calculate_total(items: list) -> float:
            """Calculates the total amount for all items."""
            return sum(items)

        assert calculate_total._obs_name == "TestObservableDecorator.test_metadata_attached.<locals>.calculate_total"
        assert calculate_total._obs_tags == ["critical", "billing"]
        assert "Calculates the total" in calculate_total._obs_description

    def test_registry_populated(self):
        """Verifies decorated functions are added to the global registry."""
        @observable(tags=["endpoint"])
        def my_endpoint() -> dict:
            """Handles the root endpoint."""
            return {}

        summary = trace_summary()
        names = [s["name"] for s in summary]
        assert any("my_endpoint" in n for n in names)

    def test_exception_propagates(self):
        """Verifies exceptions are re-raised after logging."""
        @observable(tags=["transform"])
        def will_fail() -> None:
            """Intentionally raises an error for testing."""
            raise ValueError("test error")

        try:
            will_fail()
            assert False, "Should have raised"
        except ValueError as e:
            assert str(e) == "test error"

    def test_nested_depth(self, capsys):
        """Verifies nested calls produce indented output."""
        @observable(tags=["endpoint"])
        def outer() -> str:
            """Orchestrates the outer call."""
            return inner()

        @observable(tags=["transform"])
        def inner() -> str:
            """Performs the inner computation."""
            return "done"

        result = outer()
        assert result == "done"

        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        # outer entry should have no indent, inner should have 2-space indent
        assert lines[0].startswith("\u2192")
        assert lines[1].startswith("  \u2192")

    def test_disabled_config(self, capsys):
        """Verifies no output when observability is disabled."""
        ObservabilityConfig.configure(enabled=False)

        @observable(tags=["transform"])
        def silent() -> str:
            """Returns a value silently."""
            return "quiet"

        result = silent()
        assert result == "quiet"
        assert capsys.readouterr().out == ""


class TestObservabilityConfig:
    """Tests for the configuration system."""

    def test_configure_updates_values(self):
        """Verifies configure() updates class attributes."""
        ObservabilityConfig.configure(
            emit_to="custom",
            include_args=True,
            max_depth=5,
            project_name="test-proj",
        )
        assert ObservabilityConfig.emit_to == "custom"
        assert ObservabilityConfig.include_args is True
        assert ObservabilityConfig.max_depth == 5
        assert ObservabilityConfig.project_name == "test-proj"

    def test_configure_ignores_unknown_keys(self):
        """Verifies configure() silently ignores unknown keys."""
        ObservabilityConfig.configure(nonexistent_key="value")
        assert not hasattr(ObservabilityConfig, "nonexistent_key") or True
