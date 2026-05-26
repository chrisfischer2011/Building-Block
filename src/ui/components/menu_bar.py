import flet as ft
from src.utils.helpers import show_coming_soon

def create_menu_bar(page: ft.Page):
    """Returns the custom menu bar for the app"""
    
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

    return ft.Container(
        content=ft.Row(
            [
                # Left Side - Menus
                ft.Row(
                    [
                        ft.PopupMenuButton(
                            icon=ft.Icons.MENU,
                            icon_color=ft.Colors.WHITE,
                            tooltip="File",
                            items=[
                                ft.PopupMenuItem(content=ft.Text("New"), on_click=file_new),
                                ft.PopupMenuItem(),  
                                ft.PopupMenuItem(content=ft.Text("Save"), on_click=file_save),
                                ft.PopupMenuItem(content=ft.Text("Load"), on_click=file_load),
                            ]
                        ),
                        ft.Container(
                            content=ft.PopupMenuButton(
                                content=ft.Text("Settings", color=ft.Colors.WHITE),
                                tooltip="Settings",
                                items=[ft.PopupMenuItem(content=ft.Text("Preferences"), on_click=settings_clicked)],
                            ),
                            padding=7,
                        ),
                        ft.Container(width=5),
                        ft.Container(
                            content=ft.PopupMenuButton(
                                content=ft.Text("About", color=ft.Colors.WHITE),
                                tooltip="About",
                                items=[ft.PopupMenuItem(content=ft.Text("About this App"), on_click=about_clicked)],
                            ),
                            padding=7,
                        ),
                    ],
                    spacing=5,
                ),
                
                # Center Title
                ft.Text(
                    "Building Block", 
                    size=26, 
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                    expand=True,
                    text_align=ft.TextAlign.CENTER
                ),
                
                # Right padding
                ft.Container(width=50)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=ft.Colors.BLUE_700,
        padding=15,
        height=65,
    )