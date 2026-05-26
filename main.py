import flet as ft
from src.core.database import init_database
from src.utils.helpers import show_coming_soon
from src.ui.components.menu_bar import create_menu_bar   #Menu Bar

def main(page: ft.Page):
    page.title = "Building Block - Data App"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window_width = 1350
    page.window_height = 800
    page.expand = True

    # Initialize Database
    init_database()

    # ==================== MAIN CONTENT ====================
    status = ft.Text("Status: Ready", color=ft.Colors.GREEN_700, size=14)

    def test_clicked(e):
        show_coming_soon(page, "Test Data Tools")

    test_button = ft.Button(
        "Test Button (Future Tools)",
        on_click=test_clicked,
        bgcolor=ft.Colors.BLUE_700,
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
    )

    main_content = ft.Column(
        [
            ft.Text("Main Content Area - Tables & Forms will go here", 
                    size=18, weight=ft.FontWeight.BOLD),
            test_button,
            status,
        ],
        spacing=20,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )

    # Final Layout
    page.add(
        ft.Column(
            [
                create_menu_bar(),
                ft.Container(content=main_content, padding=20, expand=True),
            ],
            expand=True,
        )
    )

if __name__ == "__main__":
    ft.app(target=main)