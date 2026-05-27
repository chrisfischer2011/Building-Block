"""
Legacy helpers module.

Most new feedback utilities live in src/utils/feedback.py.
This file re-exports show_coming_soon for backward compatibility.
"""

from src.utils.feedback import show_coming_soon  # noqa: F401

# Note: The old dialog-based implementation has been replaced with a
# SnackBar-first approach (much better during development).
# Use show_coming_soon(page, "Feature") — it now shows a SnackBar by default.