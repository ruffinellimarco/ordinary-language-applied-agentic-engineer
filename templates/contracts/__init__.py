"""
contracts/__init__.py
Vendored observability contract — no external dependencies required.
"""
from .observable import observable, ObservabilityConfig, trace_summary, _registry

__all__ = ["observable", "ObservabilityConfig", "trace_summary", "_registry"]
