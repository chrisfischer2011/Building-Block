import flet as ft
from src.core.database import clear_all_data
from src.ui.theme import HEADER_ELEVATION, HEADER_HEIGHT, HEADER_MENU_SPACING, HEADER_PADDING
from src.utils.feedback import show_coming_soon, show_success

def create_menu_bar(page: ft.Page):
    """Creates the top application header bar.
    
    Features:
    - Theme-driven colors, spacing, and elevation
    - Robust three-section layout (menus / title / spacer)
    - Consistent text-based menu triggers
    - Subtle shadow for visual separation
    """
    
    def file_new(e): 
        """File > New: completely clears all Rack/Amplifier data and resets UI panels."""
        try:
            # 1. Remove all working data from the database (fresh slate)
            clear_all_data()
        except Exception as ex:
            print(f"[File > New] clear_all_data failed: {ex}")

        # 2. Tell AppState to clear selection + fire all registered refresh callbacks
        #    (sidebar will rebuild empty list, inspector will show "No item selected")
        if hasattr(page, "_app_state"):
            page._app_state.clear()
        else:
            # Fallback direct mutation (should not normally happen)
            # This path won't refresh the visual lists because no callbacks registered
            pass

        # 3. Force a top-level update (callbacks usually do their own, this is belt-and-suspenders)
        try:
            page.update()
        except Exception:
            pass

        # Optional user feedback (non-blocking)
        try:
            show_success(page, "New project started — all data cleared")
        except Exception:
            pass

    def file_save(e): 
        show_coming_soon(page, "Save")

    def file_load(e): 
        show_coming_soon(page, "Load")

    def settings_clicked(e): 
        show_coming_soon(page, "Settings")

    def about_clicked(e): 
        show_coming_soon(page, "About this App")

    # Pull colors from the active theme
    color_scheme = page.theme.color_scheme
    header_bg = color_scheme.primary
    header_text = color_scheme.on_primary

    # Header content (inner container handles styling)
    header_content = ft.Container(
        content=ft.Row(
            [
                # Left section - Menus (standardized text-based triggers)
                ft.Row(
                    [
                        ft.PopupMenuButton(
                            content=ft.Text("File", color=header_text),
                            tooltip="File",
                            items=[
                                ft.PopupMenuItem(content=ft.Text("New"), on_click=file_new),
                                ft.PopupMenuItem(),  
                                ft.PopupMenuItem(content=ft.Text("Save"), on_click=file_save),
                                ft.PopupMenuItem(content=ft.Text("Load"), on_click=file_load),
                            ],
                        ),
                        ft.PopupMenuButton(
                            content=ft.Text("Settings", color=header_text),
                            tooltip="Settings",
                            items=[
                                ft.PopupMenuItem(content=ft.Text("Preferences"), on_click=settings_clicked),
                            ],
                        ),
                        ft.PopupMenuButton(
                            content=ft.Text("About", color=header_text),
                            tooltip="About",
                            items=[
                                ft.PopupMenuItem(content=ft.Text("About this App"), on_click=about_clicked),
                            ],
                        ),
                    ],
                    spacing=HEADER_MENU_SPACING,
                    expand=1,
                ),
                
                # Center Title - Better visual centering
                ft.Container(
                    content=ft.Text(
                        "Building Block",
                        size=26,
                        weight=ft.FontWeight.BOLD,
                        color=header_text,
                    ),
                    expand=2,
                    alignment=ft.Alignment.CENTER,
                ),
                
                # Right section (spacer for balance - can hold future actions)
                ft.Container(expand=1),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=header_bg,
        padding=HEADER_PADDING,
        height=HEADER_HEIGHT,
        border=ft.Border(
            bottom=ft.BorderSide(width=1, color=color_scheme.outline)
        ),
    )

    # Use Card to provide elevation (Container does not support 'elevation' in Flet 0.85)
    return ft.Card(
        content=header_content,
        elevation=HEADER_ELEVATION,
        margin=0,           # Full width, no default card margins
    )