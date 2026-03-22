"""
observability_contracts.core
============================
Universal @observable decorator for self-describing functions at runtime.

Every function decorated with @observable will:
  - Emit its docstring description on entry
  - Show nested call depth (indented trace)
  - Report execution time on exit
  - Capture and re-raise errors with full context
  - Work with both sync and async functions

Install:  pip install observability-contracts
Usage:    from observability_contracts import observable
"""

import asyncio
import functools
import time
import logging
import contextvars
from typing import Optional, Callable, Any

# ── Trace context (tracks call depth across nested calls) ──────────────────
_call_depth = contextvars.ContextVar("_obs_call_depth", default=0)

# ── Registry of all @observable functions (replaces gc.get_objects scan) ────
_registry: list[dict] = []

logger = logging.getLogger("obs")

# ── Cached GCP client (created once, reused) ──────────────────────────────
_gcp_client = None
_gcp_logger = None


class ObservabilityConfig:
    """
    Global configuration singleton for the observability system.

    Configure once at app startup:
        ObservabilityConfig.configure(emit_to="cloud_logging", include_args=True)
    """

    enabled: bool = True
    emit_to: str = "stdout"              # "stdout" | "cloud_logging" | "custom"
    custom_emitter: Optional[Callable] = None
    include_args: bool = False           # Log function args (watch for PII)
    include_return: bool = False         # Log return values
    max_depth: int = 20                  # Circuit breaker for deep recursion
    project_name: str = ""              # Shown in cloud_logging structured logs

    @classmethod
    def configure(cls, **kwargs):
        """Applies configuration options to the global observability config."""
        for k, v in kwargs.items():
            if hasattr(cls, k):
                setattr(cls, k, v)


def _get_gcp_logger():
    """Returns a cached GCP Cloud Logging logger instance."""
    global _gcp_client, _gcp_logger
    if _gcp_logger is None:
        from google.cloud import logging as gcp_logging
        _gcp_client = gcp_logging.Client()
        _gcp_logger = _gcp_client.logger("obs-trace")
    return _gcp_logger


def _emit(message: str, level: str = "INFO", metadata: dict = None):
    """Routes log emission to the configured sink."""
    if not ObservabilityConfig.enabled:
        return

    meta = metadata or {}

    if ObservabilityConfig.emit_to == "stdout":
        try:
            print(message)
        except UnicodeEncodeError:
            print(message.encode("ascii", errors="replace").decode("ascii"))

    elif ObservabilityConfig.emit_to == "cloud_logging":
        try:
            cl = _get_gcp_logger()
            cl.log_struct({"message": message, "level": level, **meta})
        except ImportError:
            print("[obs] google-cloud-logging not installed, falling back to stdout")
            print(message)

    elif ObservabilityConfig.emit_to == "custom" and ObservabilityConfig.custom_emitter:
        ObservabilityConfig.custom_emitter(message, level, meta)

    else:
        getattr(logger, level.lower(), logger.info)(message)


def _build_meta(display_name, description, depth, func_tags):
    """Builds the metadata dict shared by entry/exit/error phases."""
    meta = {
        "function": display_name,
        "description": description,
        "depth": depth,
        "tags": func_tags,
        "project": ObservabilityConfig.project_name,
    }
    return meta


def _on_entry(indent, display_name, description, func_tags, meta, args, kwargs):
    """Emits the entry log for a function call."""
    tag_str = f"  [{', '.join(func_tags)}]" if func_tags else ""
    entry_msg = f"{indent}\u2192 {display_name}: \"{description}\"{tag_str}"

    if ObservabilityConfig.include_args:
        meta["args"] = repr(args)[:300]
        meta["kwargs"] = repr(kwargs)[:300]

    _emit(entry_msg, "INFO", {**meta, "phase": "entry"})


def _on_exit(indent, display_name, elapsed, meta, result):
    """Emits the exit log for a successful function call."""
    exit_msg = f"{indent}\u2190 {display_name}: completed in {elapsed:.3f}s"
    _emit(exit_msg, "INFO", {**meta, "phase": "exit", "duration_s": round(elapsed, 4)})

    if ObservabilityConfig.include_return:
        _emit(f"{indent}  \u21a9 return: {repr(result)[:200]}")


def _on_error(indent, display_name, elapsed, meta, exc):
    """Emits the error log for a failed function call."""
    err_msg = (
        f"{indent}\u2717 {display_name}: FAILED after {elapsed:.3f}s "
        f"\u2014 {type(exc).__name__}: {exc}"
    )
    _emit(err_msg, "ERROR", {
        **meta,
        "phase": "error",
        "duration_s": round(elapsed, 4),
        "error": str(exc),
        "error_type": type(exc).__name__,
    })


def observable(func: Callable = None, *, name: str = None, tags: list = None):
    """
    Decorator that makes any function self-describing at runtime.

    Reads the function's docstring and emits structured trace logs on
    entry, exit, and error — including call depth for nested visibility.
    Works with both sync and async functions.

    Usage (no args):
        @observable
        def fetch_accounts(period: str) -> list:
            \"\"\"Pulls active accounts from BigQuery for the given period.\"\"\"
            ...

    Usage (with tags):
        @observable(tags=["endpoint", "billing"])
        def calculate_invoice(account_id: str) -> float:
            \"\"\"Calculates the final invoice amount for an account.\"\"\"
            ...

    Usage (async):
        @observable(tags=["db"])
        async def fetch_accounts(period: str) -> list:
            \"\"\"Pulls active accounts from BigQuery for the given period.\"\"\"
            ...

    Tags reference:
        endpoint    - exposed via HTTP/API
        db          - reads or writes a database
        transform   - pure data transformation
        external-api - calls a third-party service
        critical    - business-critical path
        billing     - touches financial data
        auth        - authentication / authorization
        cache       - caching layer
    """
    if func is None:
        return lambda f: observable(f, name=name, tags=tags)

    display_name = name or func.__qualname__
    raw_doc = func.__doc__ or "No description provided."
    description = raw_doc.strip().split("\n")[0].strip()
    func_tags = tags or []

    if asyncio.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            """Async wrapper that traces coroutine execution."""
            depth = _call_depth.get()

            if depth > ObservabilityConfig.max_depth:
                return await func(*args, **kwargs)

            indent = "  " * depth
            token = _call_depth.set(depth + 1)
            meta = _build_meta(display_name, description, depth, func_tags)

            _on_entry(indent, display_name, description, func_tags, meta, args, kwargs)

            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                _on_exit(indent, display_name, elapsed, meta, result)
                return result
            except Exception as exc:
                elapsed = time.perf_counter() - start
                _on_error(indent, display_name, elapsed, meta, exc)
                raise
            finally:
                _call_depth.reset(token)

        wrapper = async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            """Sync wrapper that traces function execution."""
            depth = _call_depth.get()

            if depth > ObservabilityConfig.max_depth:
                return func(*args, **kwargs)

            indent = "  " * depth
            token = _call_depth.set(depth + 1)
            meta = _build_meta(display_name, description, depth, func_tags)

            _on_entry(indent, display_name, description, func_tags, meta, args, kwargs)

            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                _on_exit(indent, display_name, elapsed, meta, result)
                return result
            except Exception as exc:
                elapsed = time.perf_counter() - start
                _on_error(indent, display_name, elapsed, meta, exc)
                raise
            finally:
                _call_depth.reset(token)

        wrapper = sync_wrapper

    # ── Attach metadata for introspection / eval scanning ───────────────────
    wrapper._obs_name = display_name
    wrapper._obs_description = description
    wrapper._obs_tags = func_tags
    wrapper._is_observable = True

    # ── Register in the global registry ─────────────────────────────────────
    _registry.append({
        "name": display_name,
        "description": description,
        "tags": func_tags,
    })

    return wrapper


def trace_summary() -> list[dict]:
    """Returns metadata for all @observable functions registered at import time."""
    return list(_registry)
