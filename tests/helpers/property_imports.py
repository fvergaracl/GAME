try:
    from hypothesis import given, settings
    from hypothesis import strategies as st
except Exception:  # pragma: no cover - exercised only when Hypothesis unavailable.
    from tests.helpers.hypothesis_compat import given, settings
    from tests.helpers.hypothesis_compat import strategies as st

__all__ = ["given", "settings", "st"]
