"""
Test bootstrap for pytest

Ensures the repository root is on sys.path so tests can import
the `custom_components` package (the integration source) during
collection. This is a minimal, temporary shim — long-term, tests
should use Home Assistant's test harness fixtures and not rely on
local path hacks.
"""
import os
import sys

# Insert the repository root (one level up from tests/) at the front
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

try:
    # Optional: prefer installed homeassistant fixtures if available
    import homeassistant  # noqa: F401
except Exception:
    # homeassistant may not be installed in some environments; tests that
    # require it will fail later with a clear message.
    pass
