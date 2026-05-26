import flet as ft
from src.utils.helpers import show_coming_soon

def create_main_layout(page: ft.Page):
    """Returns the main content layout (Left + Right panels)"""

    # ==================== LEFT PANEL ====================
    left_panel = ft.Container(
        content=ft.Text("Rack & Amp Selection", size=16, weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.BLUE_50,
        padding=7,
        margin=2,
        border_radius=8,
        border=ft.Border.all(2, ft.Colors.BLUE_400),
        expand=True,
        col={"xs": 4, "sm": 3, "md": 3, "lg": 2, "xl": 1.5, "xxl": 1.5}
    )

    # ==================== RIGHT PANEL (Split into Two) ====================
    # Top Panel - Orange
    top_right_panel = ft.Container(
        content=ft.Text("Edit Selected", size=15, weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.ORANGE_50,
        padding=7,
        height=60,
        margin=2,
        border=ft.Border.all(2, ft.Colors.ORANGE_400),
        border_radius=6,
        expand=False,
    )

    # Bottom Panel - Purple
    bottom_right_panel = ft.Container(
        content=ft.Text("Editable Area", size=16, weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.PURPLE_50,
        padding=7,
        margin=2,
        border=ft.Border.all(2, ft.Colors.PURPLE_400),
        border_radius=6,
        expand=True,
    )

    # Right Panel Container
    right_panel = ft.Container(
        content=ft.Column(
            [
                top_right_panel,
                bottom_right_panel,
            ],
            spacing=1,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        ),
        border=ft.Border.all(2, ft.Colors.BLUE_400),
        border_radius=8,
        margin=2,
        expand=True,
        col={"xs": 8, "sm": 9, "md": 9, "lg": 10, "xl": 10.5, "xxl": 10.5}
    )

    # Main Responsive Layout
    main_content = ft.ResponsiveRow(
        [left_panel, right_panel],
        spacing=1,
        expand=True,
        columns=12,
        vertical_alignment=ft.CrossAxisAlignment.STRETCH
    )

    return main_content