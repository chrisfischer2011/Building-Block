import flet as ft

def show_coming_soon(page: ft.Page, feature_name: str = "This feature"):
    """Reusable Coming Soon dialog - Compatible with Flet 0.85.1"""
    
    def close_dlg(e):
        page.pop_dialog()        # Best method for v0.85+
        # Alternative: page.close_dialog()

    dlg = ft.AlertDialog(
        title=ft.Text("Coming Soon"),
        content=ft.Text(f"{feature_name} is under development.\n\nStay tuned!"),
        actions=[
            ft.TextButton("OK", on_click=close_dlg)
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    # Open the dialog
    page.show_dialog(dlg)