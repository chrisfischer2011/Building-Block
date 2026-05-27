"""
Feedback utilities for the Building Block app.

Provides consistent, non-intrusive user feedback using SnackBars for
transient messages and keeps AlertDialog available for important cases.

Usage examples:
    from src.utils.feedback import (
        show_snackbar, show_success, show_error, show_info, show_warning,
        show_coming_soon
    )

    show_success(page, "Data saved successfully")
    show_coming_soon(page, "Export to Excel")
"""

import flet as ft
from typing import Optional


# ============================================================
# Core SnackBar primitive
# ============================================================

def show_snackbar(
    page: ft.Page,
    message: str,
    *,
    duration: int = 4000,
    bgcolor: Optional[ft.Colors] = None,
    text_color: Optional[ft.Colors] = None,
    action: Optional[str] = None,
    on_action: Optional[callable] = None,
    show_close_icon: bool = False,
) -> None:
    """
    Show a transient SnackBar message.

    This is the preferred method for most user feedback during development
    and normal operation (much less disruptive than dialogs).

    Args:
        page: The current Flet page.
        message: The text to display.
        duration: How long to show the snackbar in milliseconds.
        bgcolor: Optional background color. Defaults to a theme-appropriate color.
        text_color: Optional text color.
        action: Optional action button text (e.g. "Undo").
        on_action: Callback when the action button is clicked.
        show_close_icon: Whether to show a close (X) icon.
    """
    content = ft.Text(message, color=text_color)

    snack_bar = ft.SnackBar(
        content=content,
        duration=duration,
        bgcolor=bgcolor,
        show_close_icon=show_close_icon,
        action=action,
        on_action=on_action,
        behavior=ft.SnackBarBehavior.FLOATING,
    )

    # Correct way to show SnackBar in Flet 0.85.2:
    # We append SnackBars to page.overlay (the proper mechanism in this version).
    # Clean up any previous SnackBars to avoid accumulation.
    page.overlay[:] = [ctrl for ctrl in page.overlay if not isinstance(ctrl, ft.SnackBar)]

    snack_bar.open = True
    page.overlay.append(snack_bar)
    page.update()


# ============================================================
# Convenience wrappers (recommended for most use cases)
# ============================================================

def show_success(page: ft.Page, message: str, **kwargs) -> None:
    """Show a success message (green snackbar)."""
    show_snackbar(
        page,
        message,
        bgcolor=ft.Colors.GREEN_700,
        text_color=ft.Colors.WHITE,
        **kwargs,
    )


def show_error(page: ft.Page, message: str, **kwargs) -> None:
    """Show an error message (red snackbar)."""
    show_snackbar(
        page,
        message,
        bgcolor=ft.Colors.RED_700,
        text_color=ft.Colors.WHITE,
        duration=6000,  # Errors stay a bit longer by default
        **kwargs,
    )


def show_warning(page: ft.Page, message: str, **kwargs) -> None:
    """Show a warning message (amber/orange snackbar)."""
    show_snackbar(
        page,
        message,
        bgcolor=ft.Colors.AMBER_700,
        text_color=ft.Colors.BLACK,
        **kwargs,
    )


def show_info(page: ft.Page, message: str, **kwargs) -> None:
    """Show an informational message (uses app primary color)."""
    show_snackbar(
        page,
        message,
        bgcolor=ft.Colors.BLUE_700,
        text_color=ft.Colors.WHITE,
        **kwargs,
    )


# ============================================================
# Coming Soon helper (updated for better developer experience)
# ============================================================

def show_coming_soon(
    page: ft.Page,
    feature_name: str = "This feature",
    *,
    as_dialog: bool = False,
) -> None:
    """
    Notify the user that a feature is not yet implemented.

    By default this now uses a SnackBar (much less annoying during development).
    Set as_dialog=True if you need a blocking modal for a specific case.

    Args:
        page: The current Flet page.
        feature_name: Name of the feature being accessed.
        as_dialog: If True, shows a traditional AlertDialog instead of a SnackBar.
    """
    message = f"{feature_name} is coming soon!"

    if as_dialog:
        def close_dlg(e):
            page.pop_dialog()

        dlg = ft.AlertDialog(
            title=ft.Text("Coming Soon"),
            content=ft.Text(f"{feature_name} is under development.\n\nStay tuned!"),
            actions=[
                ft.TextButton("OK", on_click=close_dlg)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.show_dialog(dlg)
    else:
        # Preferred path: non-blocking SnackBar
        show_snackbar(
            page,
            message,
            bgcolor=ft.Colors.BLUE_GREY_700,
            text_color=ft.Colors.WHITE,
            duration=3000,
        )
