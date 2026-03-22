"""
src/main.py
===========
Starter entrypoint — demonstrates the @observable pattern with nested call chain.
Replace with your actual application logic.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contracts.observable import observable, ObservabilityConfig

# ── Configure once at startup ──────────────────────────────────────────────
ObservabilityConfig.configure(
    emit_to="stdout",
    project_name="my-project",
)


@observable(tags=["endpoint"])
def handle_request(payload: dict) -> dict:
    """Handles the main incoming request and orchestrates processing."""
    validated = validate_payload(payload)
    result = process_data(validated)
    return {"status": "ok", "result": result}


@observable(tags=["transform"])
def validate_payload(payload: dict) -> dict:
    """Validates and normalizes the incoming request payload."""
    if "data" not in payload:
        raise ValueError("Missing 'data' field in payload")
    return {k: str(v).strip() for k, v in payload.items()}


@observable(tags=["transform"])
def process_data(data: dict) -> list:
    """Processes validated data and returns a list of results."""
    items = extract_items(data)
    return [transform_item(item) for item in items]


@observable(tags=["transform"])
def extract_items(data: dict) -> list:
    """Extracts individual items from the normalized data payload."""
    return data.get("data", "").split(",")


def transform_item(item: str) -> str:
    """Transforms a single item to uppercase and strips whitespace."""
    return item.strip().upper()


if __name__ == "__main__":
    print("\n=== Observable Call Chain Demo ===\n")
    response = handle_request({"data": "alpha, beta, gamma"})
    print(f"\nResponse: {response}")
    print("\n=== End Demo ===\n")
