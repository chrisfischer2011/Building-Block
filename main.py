import flet as ft
from src.core.database import init_database
from src.utils.helpers import show_coming_soon

def main(page: ft.Page):
    page.title = "Building Block - Data App"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window_width = 1200
    page.window_height = 800
    page.expand = True

    # Initialize Database
    init_database()

    # ==================== MENU ACTIONS ====================
    def file_new(e): 
        show_coming_soon(page, "New File")

    def file_save(e): 
        show_coming_soon(page, "Save")

    def file_load(e): 
        show_coming_soon(page, "Load")

    def settings_clicked(e): 
        show_coming_soon(page, "Settings")

    def about_clicked(e): 
        show_coming_soon(page, "About this App")

    # ==================== MENU BAR ====================
    menu_bar = ft.AppBar(
        title=ft.Text("Building Block"),
        bgcolor=ft.Colors.BLUE_700,
        color=ft.Colors.WHITE,
        actions=[
            ft.PopupMenuButton(
                icon=ft.Icons.MENU,
                tooltip="File",
                items=[
                    ft.PopupMenuItem(content=ft.Text("New"), on_click=file_new),
                    ft.PopupMenuItem(),  
                    ft.PopupMenuItem(content=ft.Text("Save"), on_click=file_save),
                    ft.PopupMenuItem(content=ft.Text("Load"), on_click=file_load),
                ]
            ),
            ft.PopupMenuButton(
                content=ft.Text("Settings"),
                tooltip="Settings",
                items=[ft.PopupMenuItem(content=ft.Text("Preferences"), on_click=settings_clicked)],
            ),
            ft.PopupMenuButton(
                content=ft.Text("About"),
                tooltip="About",
                items=[ft.PopupMenuItem(content=ft.Text("About this App"), on_click=about_clicked)],
            ),
        ]
    )

    # Main Content Area
    status = ft.Text("Status: Ready", color=ft.Colors.GREEN_700, size=14)

    def test_clicked(e):
        show_coming_soon(page, "Test Data Tools")

    test_button = ft.ElevatedButton(
        "Test Button (Future Tools)",
        on_click=test_clicked,
        bgcolor=ft.Colors.BLUE_700,
        color=ft.Colors.WHITE,
    )

    main_content = ft.Column(
        [
            ft.Text("Main Content Area", size=18, weight=ft.FontWeight.BOLD),
            test_button,
            status,
        ],
        spacing=20,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )

    page.add(
        ft.Column(
            [menu_bar, ft.Container(content=main_content, padding=20, expand=True)],
            expand=True,
        )
    )

if __name__ == "__main__":
    ft.app(target=main)