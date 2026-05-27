import flet as ft
from src.core.database import init_database
from src.ui.components.menu_bar import create_menu_bar
from src.ui.main_layout import create_main_layout
from src.ui.theme import CONTENT_PADDING, create_app_theme
from src.utils.helpers import show_coming_soon

def main(page: ft.Page):
    page.title = "Building Block - Data App"
    page.theme = create_app_theme()
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    # Window sizing & constraints
    page.window_width = 1200
    page.window_height = 750
    page.window_min_width = 1000
    page.window_min_height = 650
    page.window_resizable = True

    init_database()

    # Final Page Layout
    page.add(
        ft.Column(
            [
                create_menu_bar(page),
                ft.Container(
                    content=create_main_layout(page),
                    padding=CONTENT_PADDING,
                    expand=True
                ),
            ],
            expand=True,
        )
    )

if __name__ == "__main__":
    ft.app(target=main)

    