import flet as ft
from src.core.database import init_database
from src.ui.components.menu_bar import create_menu_bar
from src.utils.helpers import show_coming_soon

def main(page: ft.Page):
    page.title = "Building Block - Data App"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window_width = 1350
    page.window_height = 800
    page.expand = True

    init_database()

    # ==================== LEFT PANEL ====================
    left_panel = ft.Container(
        content=ft.Text("Rack & Amp Selection", size=16, weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.BLUE_50,
        padding=15,
        margin=2,
        border_radius=8,
        border=ft.Border(
            left=ft.BorderSide(2, ft.Colors.BLUE_400),
            top=ft.BorderSide(2, ft.Colors.BLUE_400),
            right=ft.BorderSide(2, ft.Colors.BLUE_400),
            bottom=ft.BorderSide(2, ft.Colors.BLUE_400),
        ),
        expand=True,
        col={"xs": 4, "sm": 3, "md": 3, "lg": 2, "xl": 1.5, "xxl": 1.5}
    )

    # ==================== RIGHT PANEL (Split into Two) ====================
    # Top Panel - Orange, small but scalable height
    top_right_panel = ft.Container(
        content=ft.Text("Edit Selected", size=15, weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.ORANGE_50,
        padding=10,
        height=100,                    # Starting height (~30-60 range)
        
        margin=2,
        border=ft.Border(
            left=ft.BorderSide(2, ft.Colors.ORANGE_400),
            top=ft.BorderSide(2, ft.Colors.ORANGE_400),
            right=ft.BorderSide(2, ft.Colors.ORANGE_400),
            bottom=ft.BorderSide(2, ft.Colors.ORANGE_400),
        ),
        border_radius=6,
        expand_loose=True,                 # Fixed height but can grow
    )

    # Bottom Panel - Purple, takes remaining space
    bottom_right_panel = ft.Container(
        content=ft.Text("Editable Area", size=16, weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.PURPLE_50,
        padding=20,
        margin=2,
        border=ft.Border(
            left=ft.BorderSide(2, ft.Colors.PURPLE_400),
            top=ft.BorderSide(2, ft.Colors.PURPLE_400),
            right=ft.BorderSide(2, ft.Colors.PURPLE_400),
            bottom=ft.BorderSide(2, ft.Colors.PURPLE_400),
        ),
        border_radius=6,
        expand=True,                  # Takes all remaining height
    )

    # Right Panel Container (contains both sub-panels)
    right_panel = ft.Container(
        content=ft.Column(
            [
                top_right_panel,
                bottom_right_panel,
            ],
            spacing=8,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        ),
        border=ft.Border(
            left=ft.BorderSide(2, ft.Colors.BLUE_400),
            top=ft.BorderSide(2, ft.Colors.BLUE_400),
            right=ft.BorderSide(2, ft.Colors.BLUE_400),
            bottom=ft.BorderSide(2, ft.Colors.BLUE_400),
        ),
        border_radius=8,
        margin=2,
        expand=True,
        col={"xs": 8, "sm": 9, "md": 9, "lg": 10, "xl": 10.5, "xxl": 10.5},
    )

    # Main Responsive Layout
    main_content = ft.ResponsiveRow(
        [
            left_panel,
            right_panel,
        ],
        spacing=10,
        expand=True,
        columns=12,
        vertical_alignment=ft.CrossAxisAlignment.STRETCH
    )

    # Final Page Layout
    page.add(
        ft.Column(
            [
                create_menu_bar(page),
                ft.Container(
                    content=main_content,
                    padding=10,
                    expand=True
                ),
            ],
            expand=True,
        )
    )

if __name__ == "__main__":
    ft.app(target=main)