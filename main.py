import flet as ft
from src.core.database import init_database
from src.ui.components.menu_bar import create_menu_bar
from src.ui.main_layout import create_main_layout   # ← New Import
from src.utils.helpers import show_coming_soon

def main(page: ft.Page):
    page.title = "Building Block - Data App"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window_width = 1350
    page.window_height = 800
    page.expand = True

    init_database()

    # Final Page Layout
    page.add(
        ft.Column(
            [
                create_menu_bar(page),
                ft.Container(
                    content=create_main_layout(page),
                    padding=10,
                    expand=True
                ),
            ],
            expand=True,
        )
    )

if __name__ == "__main__":
    ft.app(target=main)