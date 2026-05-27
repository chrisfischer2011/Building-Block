import flet as ft

# ============================================
# Design Tokens - Theming & Visual Consistency
# ============================================

# Core layout tokens (things Flet Theme doesn't directly control in v0.85)
BORDER_RADIUS = 10
HEADER_HEIGHT = 65

# Header-specific tokens
HEADER_PADDING = 15
HEADER_MENU_SPACING = 8
HEADER_ELEVATION = 4

# General spacing & padding
CONTENT_PADDING = 12  # Increased for better overall breathing room
CARD_CONTENT_PADDING = 16
CARD_MARGIN = 6  # Slightly increased for better panel separation
PANEL_SPACING = 12  # Increased for better breathing room between panels

# Component-specific spacing tokens (for consistency across panels)
LIST_ITEM_SPACING = 6
FORM_SPACING = 10
EMPTY_STATE_PADDING = 30

# MAIN_CONTENT_SPACING = 8   # Currently unused after Phase 5 refactor

# Elevation
CARD_ELEVATION = 2
CARD_ELEVATION_LOW = 1


def create_app_theme() -> ft.Theme:
    """
    Returns the application theme with a cohesive ColorScheme.
    Panel backgrounds are intentionally mapped to container colors so the
    entire UI can be re-skinned by changing the theme in one place.
    """
    return ft.Theme(
        color_scheme=ft.ColorScheme(
            # Main brand (used for header and left panel)
            primary=ft.Colors.BLUE_700,
            on_primary=ft.Colors.WHITE,
            primary_container=ft.Colors.BLUE_50,        # Left "Rack & Amp Selection" panel
            on_primary_container=ft.Colors.BLUE_900,

            # Secondary (warm accent for editing actions)
            secondary=ft.Colors.AMBER_700,
            on_secondary=ft.Colors.BLACK,
            secondary_container=ft.Colors.AMBER_50,     # "Edit Selected" panel
            on_secondary_container=ft.Colors.AMBER_900,

            # Tertiary (distinct area for main content)
            tertiary=ft.Colors.INDIGO_600,
            on_tertiary=ft.Colors.WHITE,
            tertiary_container=ft.Colors.INDIGO_50,     # "Editable Area" panel
            on_tertiary_container=ft.Colors.INDIGO_900,

            # Surfaces
            surface=ft.Colors.WHITE,
            on_surface=ft.Colors.BLACK87,

            # General
            outline=ft.Colors.BLUE_200,
            shadow=ft.Colors.BLACK26,
        ),
        text_theme=ft.TextTheme(
            body_medium=ft.TextStyle(size=14),
            title_medium=ft.TextStyle(size=16, weight=ft.FontWeight.W_500),
        ),
        # Future: button themes, etc. can be added here
    )
