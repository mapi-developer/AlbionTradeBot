import flet as ft

class GuiStyle:
    class Colors:
        # Base Palette
        TRANSPARENT = "#ffffff00"
        WHITE = "#ffffff"
        WHITE_70 = "#b3ffffff" # 70% White
        WHITE_24 = "#3dffffff" # 24% White
        GREY_TEXT = "#94a3b8"
        GREY_BORDER = "#CDC7C7"
        
        DARK_BLUE = "#0f1c31"      # Main Page Background (from Login)
        GRAY_BLUE = "#1c2f4d"      # Header / Sidebar
        LIGHT_BLUE = "#2D4F78"     # Cards / Content Areas (from Login Card)
        OCEAN_BLUE = "#0C2E5D"
        DEEP_BLUE = "#203064"      # Inner Input Fields / Graphs
        
        ACCENT_BLUE = "#1d9dec"    # Primary Actions
        ACCENT_GREEN = "#0d962b"   # Success Actions
        ACCENT_RED = "#b02d21"     # Destructive Actions

        # Semantic Names (Use these in pages)
        PAGE_BG = DARK_BLUE
        HEADER_BG = GRAY_BLUE
        HEADER_NAV_BUTTON_ACTIVE = OCEAN_BLUE
        SIDEBAR_BG = GRAY_BLUE
        CARD_BG = LIGHT_BLUE
        INNER_BG = DEEP_BLUE
        TEXT_PRIMARY = WHITE
        TEXT_SECONDARY = GREY_TEXT
        BORDER_DEFAULT = WHITE_24

    class TextSize:
        TITLE = 20
        SUBTITLE = 16
        NORMAL = 14
        SMALL = 12

    # Standard Button Styles
    BUTTON_PRIMARY = ft.ButtonStyle(
        color=Colors.WHITE,
        bgcolor=Colors.ACCENT_BLUE,
        shape=ft.RoundedRectangleBorder(radius=8),
        padding=15,
    )

    BUTTON_GHOST = ft.ButtonStyle(
        color=Colors.WHITE,
        bgcolor=ft.Colors.TRANSPARENT,
        shape=ft.RoundedRectangleBorder(radius=8),
        elevation=0,
    )
    
    # Settings Specific
    SETTINGS_SAVE_BUTTON = ft.ButtonStyle(
        color=Colors.WHITE,
        bgcolor=Colors.ACCENT_GREEN,
        shape=ft.RoundedRectangleBorder(radius=8),
        text_style=ft.TextStyle(size=TextSize.TITLE, weight=ft.FontWeight.BOLD),
        alignment=ft.alignment.center,
    )

    SETTINGS_TOP_BAR_BUTTON = ft.ButtonStyle(
        color=Colors.WHITE,
        bgcolor=ft.Colors.TRANSPARENT,
        shape=ft.RoundedRectangleBorder(radius=4),
        text_style=ft.TextStyle(size=TextSize.TITLE, weight=ft.FontWeight.BOLD),
        elevation=0,
    )