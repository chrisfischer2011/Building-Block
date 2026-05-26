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

    # ==================== RESPONSIVE ROW LAYOUT ====================

    # Left Panel - Rack & Amp Selection
    left_panel = ft.Container(
        content=ft.Text("Rack & Amp Selection", size=16, weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.BLUE_50,
        padding=15,
        border_radius=8,
        col={"sm": 3, "md": 3, "lg": 2},   # Narrow on large screens
        expand=False
    )

    # Right Panel - Main Content Area
    right_panel = ft.Container(
        content=ft.Text("More Stuff", size=16, weight=ft.FontWeight.BOLD),                       # Empty for now
        bgcolor=ft.Colors.PURPLE_50,
        padding=20,
        border_radius=8,
        col={"sm": 9, "md": 9, "lg": 10},   # Takes most of the space
        expand=True
    )

    # Main Responsive Layout
    main_content = ft.ResponsiveRow(
        [
            left_panel,
            right_panel,
        ],
        spacing=10,
        expand=False,
        columns=12
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