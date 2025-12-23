from typing import Callable
import flet as ft
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from components.style import GuiStyle
from managers.config import ConfigManager, AVALIABLE_LANGUAGES, CITIES, BUY_MODES


class SettingsDropdown(ft.Dropdown):
    def __init__(
            self, 
            label: str, 
            tooltip: str, 
            options: list[ft.DropdownOption], 
            filter: bool = False, 
            value: str = "", 
            data = None, 
            save_callback: Callable = None
        ):
        super().__init__(
            label = label,
            tooltip = tooltip,
            options = options,
            dense=True,
            expand=True,
            col={"sm": 12, "md": 6, "xl": 4},
            filled=True,
            fill_color=GuiStyle.Colors.GRAY_BLUE,
            color=ft.Colors.WHITE,
            text_style=ft.TextStyle(color=ft.Colors.WHITE),
            label_style=ft.TextStyle(color=ft.Colors.WHITE),
            enable_filter=filter,
            border_color=ft.Colors.WHITE24,
            border_width=1,
            border_radius=4,
            focused_border_color=ft.Colors.WHITE,
            focused_border_width=2,
            value=value,
            data=data,
            on_change=save_callback
        )


class GeneralSettings(ft.Container):
    def __init__(self, config: ConfigManager, save_callback: Callable):
        super().__init__()
        self.save_callback = save_callback
        general_settings = config.get("general")

        self.padding = 20
        self.col={"sm": 12, "md": 4, "xl": 4}

        self.buy_mode = SettingsDropdown(
            value=general_settings["buy_mode"],
            data="buy_mode",
            label="Buy Mode Strategy", 
            tooltip="Choose strategy for bot",
            options=BUY_MODES,
            save_callback=save_callback
        )

        self.game_language = SettingsDropdown(
            value=general_settings["game_language"],
            data="game_language",
            label="Language in Game",
            tooltip="Choose your in game Language",
            options = [ft.DropdownOption(key=language, text=language) for language in AVALIABLE_LANGUAGES],
            save_callback=save_callback
        )

        self.stop_silver_threshold = ft.TextField(
            value=general_settings["min_silver"],
            data="min_silver",
            label="Stop if Silver lower Than",
            tooltip="Bot will stop if your silver will be lower",
            color=ft.Colors.WHITE,
            label_style=ft.TextStyle(color=ft.Colors.WHITE),
            fill_color=GuiStyle.Colors.DARK_BLUE,
            border_color=GuiStyle.Colors.LIGHT_GRAY_BLUE,
            on_change=save_callback
        )

        self.content = ft.ResponsiveRow(
            controls=[
                ft.Column(
                    controls = [
                        self.buy_mode,
                        self.game_language,
                        self.stop_silver_threshold,
                    ],
                    col=12,
                )
            ],
        )


class BuyLogicItem(ft.Container):
    def __init__(self, index, on_remove, save_callback: Callable):
        super().__init__()
        self.bgcolor = GuiStyle.Colors.DARK_BLUE
        self.border = ft.border.all(1, GuiStyle.Colors.BLUE)
        self.border_radius = 6
        self.index = index
        self.on_remove = on_remove
        
        self.quantity_input = ft.TextField(
            label="Quantity",
            data="amount_to_buy",
            dense=True,
            text_size=15,
            content_padding=10,
            border_color=GuiStyle.Colors.LIGHT_GRAY_BLUE,
            col={"sm": 2, "md": 2, "xl": 2},
            on_change=save_callback
        )
        
        self.price_input = ft.TextField(
            label="Price",
            data="price_larger_then",
            dense=True,
            text_size=15,
            content_padding=10,
            border_color=GuiStyle.Colors.LIGHT_GRAY_BLUE,
            col={"sm": 4, "md": 4, "xl": 4},
            on_change=save_callback
        )

        self.content = ft.ResponsiveRow(
            controls=[
                ft.ResponsiveRow(
                    controls=[
                        ft.Container(col={"sm": .1, "md": .1, "xl": .1}),
                        ft.Text(f"{self.index}.", size=12, weight=ft.FontWeight.BOLD, col={"sm": 1, "md": 1, "xl": 1}),
                        ft.Text("Buy", color="#ffffff", size=14, col={"sm": 1, "md": 1, "xl": 1}),
                        self.quantity_input,
                        ft.Text("items if price >", color="#ffffff", size=14, col={"sm": 2.5, "md": 2.5, "xl": 2.5}, text_align=ft.TextAlign.CENTER),
                        self.price_input,
                    ],
                    col={"sm": 11, "md": 11, "xl": 11},
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=ft.Colors.RED_400,
                    icon_size=18,
                    on_click=lambda _: self.on_remove(self),
                    col={"sm": 1, "md": 1, "xl": 1}
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )


class BuyLogic(ft.Container):
    def __init__(self, config: ConfigManager, current_tab: str, save_callback: Callable):
        super().__init__()
        self.config = config
        self.save_callback = save_callback
        self.current_tab = current_tab
        self.padding = ft.padding.only(10, 0, 0, 0)
        self.max_items = 20
        
        title = ft.Text(
            value="Buy Logic",
            size=14,
            weight=ft.FontWeight.BOLD,
        )

        self.counter_text = ft.Text(
            value=f"0/{self.max_items}",
            size=14,
            color=ft.Colors.GREY_400,
        )
        
        self.add_button = ft.ElevatedButton(
            text="Add New Logic",
            icon=ft.Icons.ADD,
            on_click=self.add_item,
            color="#ffffff",
            bgcolor=GuiStyle.Colors.GRAY_BLUE,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )

        self.items_column = ft.Column(spacing=1)

        scrollable_frame = ft.Column(
            controls=[self.items_column],
            height=500,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

        self.content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                title,
                                self.counter_text,
                            ]
                        ),
                        self.add_button,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(height=1, color=ft.Colors.WHITE24),
                scrollable_frame, 
            ],
            spacing=15,
        )

        self.load_items(self.current_tab)

    def load_items(self, current_tab: str):
        self.current_tab = current_tab
        self.items_column.controls.clear() 
        
        for item in self.config.get(self.current_tab).get("buy_logic", []):
            new_item = self.add_item(None)
            if new_item:
                new_item.quantity_input.value = item["amount_to_buy"]
                new_item.price_input.value = item["price_larger_then"]
        
        self.update_ui()

    def add_item(self, e) -> BuyLogicItem:
        current_count = len(self.items_column.controls)
        if current_count < self.max_items:
            new_item = BuyLogicItem(
                index=current_count + 1,
                on_remove=self.remove_item,
                save_callback=self.save_callback
            )
            self.items_column.controls.append(new_item)
            self.update_ui()
            self.save_callback()
            return new_item
        return None

    def remove_item(self, item_to_remove):
        self.items_column.controls.remove(item_to_remove)
        for i, item in enumerate(self.items_column.controls):
            new_index = i + 1
            item.index = new_index
            item.content.controls[0].controls[1].value = f"{new_index}."
        
        self.update_ui()
        self.save_callback()

    def update_ui(self):
        count = len(self.items_column.controls)
        self.counter_text.value = f"{count}/{self.max_items}"
        self.add_button.disabled = count >= self.max_items
        if self.page:
            self.update()


class RightTab(ft.Container):
    def __init__(self, config: ConfigManager, current_tab: str, save_callback: Callable):
        super().__init__()
        self.current_tab = current_tab
        self.config = config
        self.save_callback = save_callback
        self.settings = self.config.get(current_tab)
        self.bgcolor = GuiStyle.Colors.LIGHT_BLUE
        self.padding = 20
        self.col={"sm": 12, "md": 8, "xl": 8}

        self.minimal_profit_rate = ft.TextField(
            value=self.settings["min_profit_rate"],
            data="min_profit_rate",
            label="Minimal Profit Rate (%)",
            fill_color=GuiStyle.Colors.DARK_BLUE,
            text_style=ft.TextStyle(color="#ffffff"),
            label_style=ft.TextStyle(color="#ffffff"),
            border_color=GuiStyle.Colors.LIGHT_GRAY_BLUE,
            suffix_text="%",
            
            on_change=save_callback
        )

        self.default_buy_amount = ft.TextField(
            value=self.settings["default_buy_amount"],
            data="default_buy_amount",
            label="Default Buy Amount",
            fill_color=GuiStyle.Colors.DARK_BLUE,
            text_style=ft.TextStyle(color="#ffffff"),
            label_style=ft.TextStyle(color="#ffffff"),
            border_color=GuiStyle.Colors.LIGHT_GRAY_BLUE,
            suffix_text="items",
            on_change=save_callback
        )

        self.presets = ft.Container(
            content=ft.Column(
                controls=[self.create_preset_dropdown(city) for city in CITIES.keys()]
            ),
            padding=5,
            bgcolor=GuiStyle.Colors.DARK_BLUE,
            border=ft.border.all(2, GuiStyle.Colors.DARK_BLUE),
            border_radius=ft.border_radius.all(6)
        )

        base_values_title = ft.Text(
            value="Base Values",
            text_align=ft.TextAlign.END,
            weight=ft.FontWeight.BOLD
        )

        presets_title = ft.Text(
            value="Presets",
            text_align=ft.TextAlign.END,
            weight=ft.FontWeight.BOLD
        )

        self.buy_logic = BuyLogic(config=config, current_tab=self.current_tab, save_callback=self.save_callback)

        self.content = ft.ResponsiveRow(
            controls=[
                ft.Column(
                    controls = [
                        base_values_title,
                        self.minimal_profit_rate,
                        self.default_buy_amount,
                        presets_title,
                        self.presets,
                    ],
                    col={"sm": 12, "md": 5, "xl": 4},
                ),
                ft.Column(
                    controls=[
                        self.buy_logic
                    ],
                    col={"sm": 12, "md": 7, "xl": 8},
                ),
            ],
        )

    def create_preset_dropdown(self, city: str):
        dropdown = SettingsDropdown(
            value=self.settings["presets"][city],
            data=city,
            label=f"{CITIES[city]}",
            tooltip=f"Choose Preset for {CITIES[city]}",
            options = [ft.DropdownOption(key=language, text=language) for language in self.config.get_presets_list()],
            filter = True,
            save_callback=self.save_callback
        )
        return dropdown

    def update_data(self, tab_id):
        self.current_tab = tab_id
        self.settings = self.config.get(tab_id)
        
        self.minimal_profit_rate.value = self.settings.get("min_profit_rate", "0")
        self.default_buy_amount.value = self.settings.get("default_buy_amount", "0")
        self.presets.content.controls = [self.create_preset_dropdown(city) for city in CITIES.keys()]
        self.buy_logic.load_items(current_tab=self.current_tab)

        if self.page:
            self.update()


class UpperRow(ft.Container):
    def __init__(self, right_tab: RightTab):
        super().__init__()
        self.right_tab = right_tab
        self.active_tab = "fast_buy"

        def create_tab_button(text, tab_id):
            is_active = self.active_tab == tab_id
            return ft.Container(
                content=ft.ElevatedButton(
                    text=text,
                    style=GuiStyle.SETTINGS_TOP_BAR_BUTTON,
                    on_click=lambda _: self.set_active(tab_id),
                ),
                border=ft.border.only(
                    bottom=ft.BorderSide(3, ft.Colors.WHITE if is_active else ft.Colors.TRANSPARENT)
                ),
                padding=ft.padding.only(bottom=5),
            )

        self.bgcolor = GuiStyle.Colors.GRAY_BLUE
        self.padding = 10

        general_title = ft.Text(
            value="General",
            style=ft.TextStyle(
                size=GuiStyle.TextSize.SETTINGS_TITLE+5,
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.BOLD,
            )
        )
        general_title_row = ft.Container(
            padding=ft.padding.only(10, 0, 10, 0),
            content=general_title
        )

        self.fast_buy_tab_button = create_tab_button("Fast Buy", "fast_buy")
        self.order_buy_tab_button = create_tab_button("Order Buy", "order_buy")

        self.tabs_row = ft.Row(
            controls=[
                self.fast_buy_tab_button,
                self.order_buy_tab_button,
            ]
        )

        self.content = ft.ResponsiveRow(
            controls=[
                ft.Column(
                    controls=[
                        general_title_row
                    ],
                    col={"sm": 4, "md": 4, "xl": 4},
                ),
                ft.Column(
                    controls= [
                        self.tabs_row,
                    ],
                    col={"sm": 4, "md": 4, "xl": 4},
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def set_active(self, tab_id):
        self.active_tab = tab_id
        self.right_tab.update_data(tab_id)
        for i, tab_name in enumerate(["fast_buy", "order_buy"]):
            is_active = tab_name == tab_id
            self.tabs_row.controls[i].border = ft.border.only(
                bottom=ft.BorderSide(3, ft.Colors.WHITE if is_active else ft.Colors.TRANSPARENT)
            )
        self.update()


class ContentMain(ft.Container):
    def __init__(self, config: ConfigManager, save_callback: Callable):
        super().__init__()
        self.config = config
        self.general = GeneralSettings(config, save_callback=save_callback)
        self.right_tab = RightTab(config, "fast_buy", save_callback=save_callback)
        self.save_callback = save_callback

        self.content = ft.ResponsiveRow(
            controls=[
                self.general,
                self.right_tab,     
            ],
            spacing=20,
            run_spacing=20,
        )

    def update_presets(self):
        if self.right_tab:
            self.right_tab.update_data()


class Settings(ft.Container):
    def __init__(self, page: ft.Page, config: ConfigManager):
        super().__init__()
        self.margin = 0
        self.padding = 0
        self.page = page
        self.config = config

        self.content_main = None
        self.content_main = ContentMain(config=config, save_callback=self.save_all)
        self.upper_row = UpperRow(right_tab=self.content_main.right_tab)

        self.content = ft.Column(
            controls=[
                self.upper_row,
                self.content_main,
            ],
            spacing = 0,
        )

    def update_settings(self):
        return
        if self.content_main:
            self.content_main.update_presets()

    def save_all(self, e=None):
        if not self.content_main:
            return
        gen = self.content_main.general
        self.config.set("general", {
            "buy_mode": gen.buy_mode.value,
            "game_language": gen.game_language.value,
            "min_silver": gen.stop_silver_threshold.value
        })

        rt = self.content_main.right_tab
        tab_data = {
            "min_profit_rate": rt.minimal_profit_rate.value,
            "default_buy_amount": rt.default_buy_amount.value,
            "presets": {dd.data: dd.value for dd in rt.presets.content.controls},
            "buy_logic": [
                {
                    "amount_to_buy": item.quantity_input.value,
                    "price_larger_then": item.price_input.value
                } for item in rt.buy_logic.items_column.controls
            ]
        }
        self.config.set(rt.current_tab, tab_data)
        
def main(page: ft.Page):
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO
    config_manager = ConfigManager()
    app_settings = Settings(page=page, config=config_manager)
    page.add(app_settings)
    page.update()

if __name__ == "__main__":
    ft.app(target=main)