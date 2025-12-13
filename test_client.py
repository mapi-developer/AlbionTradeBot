import flet as ft
import time

# --- 1. The Actual Logic Functions ---
# These are the backend functions that will be executed based on the UI configuration.

def execute_buy_items(item_name, quantity, log_callback):
    """Simulates buying an item."""
    log_callback(f"b... Buying {quantity}x '{item_name}'...", ft.Colors.GREEN)
    time.sleep(0.5) # Simulate network request
    log_callback(f"SUCCESS: Purchased {quantity}x {item_name}", ft.Colors.GREEN_ACCENT)

def execute_remove_orders(order_id, log_callback):
    """Simulates removing an order."""
    log_callback(f"... Finding Order ID: {order_id}", ft.Colors.ORANGE)
    time.sleep(0.5)
    log_callback(f"SUCCESS: Order {order_id} removed.", ft.Colors.ORANGE_ACCENT)

def execute_check_prices(item_name, log_callback):
    """Simulates checking a price."""
    log_callback(f"... Checking price for '{item_name}'", ft.Colors.BLUE)
    import random
    price = random.randint(10, 500)
    time.sleep(0.5)
    log_callback(f"INFO: Price for {item_name} is ${price}", ft.Colors.BLUE_ACCENT)


# --- 2. The Visual Block Component ---
# This class represents a single 'block' in your Scratch-like list.

class FunctionBlock(ft.Container):
    def __init__(self, func_type, remove_callback):
        super().__init__()
        self.func_type = func_type
        self.remove_callback = remove_callback
        
        # Style settings based on function type (Scratch-like color coding)
        self.block_color = ft.Colors.GREY_800
        self.icon = ft.Icons.CIRCLE
        
        # Inputs storage
        self.inputs = {} 

        if func_type == "Buy Items":
            self.block_color = ft.Colors.INDIGO_600
            self.icon = ft.Icons.SHOPPING_CART
        elif func_type == "Remove Orders":
            self.block_color = ft.Colors.RED_700
            self.icon = ft.Icons.DELETE_FOREVER
        elif func_type == "Check Prices":
            self.block_color = ft.Colors.TEAL_600
            self.icon = ft.Icons.PRICE_CHECK

        # Setup the UI structure of the block
        self.border_radius = 10
        self.padding = 10
        self.margin = ft.margin.only(bottom=10)
        self.bgcolor = self.block_color
        
        self.content = self._build_content()

    def _build_content(self):
        """Creates the internal input fields based on the function type."""
        
        # Common elements: Icon and Title
        controls_row = [
            ft.Icon(self.icon, color=ft.Colors.WHITE),
            ft.Text(self.func_type, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, size=16),
        ]

        # Dynamic Inputs
        if self.func_type == "Buy Items":
            self.inputs['item_name'] = ft.TextField(hint_text="Item Name", height=40, text_size=14, expand=True, bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK)
            self.inputs['quantity'] = ft.TextField(hint_text="Qty", width=60, height=40, text_size=14, keyboard_type=ft.KeyboardType.NUMBER, bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK)
            
            controls_row.append(self.inputs['item_name'])
            controls_row.append(self.inputs['quantity'])

        elif self.func_type == "Remove Orders":
            self.inputs['order_id'] = ft.TextField(hint_text="Order ID", height=40, text_size=14, expand=True, bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK)
            
            controls_row.append(self.inputs['order_id'])

        elif self.func_type == "Check Prices":
            self.inputs['item_name'] = ft.TextField(hint_text="Item to Check", height=40, text_size=14, expand=True, bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK)
            
            controls_row.append(self.inputs['item_name'])

        # Delete Button (X)
        controls_row.append(
            ft.IconButton(
                icon=ft.Icons.CLOSE, 
                icon_color=ft.Colors.WHITE54, 
                tooltip="Remove Block",
                on_click=lambda _: self.remove_callback(self)
            )
        )

        return ft.Row(controls=controls_row, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def get_configuration(self):
        """Extracts the values from the text fields."""
        data = {"type": self.func_type}
        for key, field in self.inputs.items():
            data[key] = field.value
        return data


# --- 3. Main Application ---

def main(page: ft.Page):
    page.title = "Flet Visual Scripter"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    # -- UI Components --

    # 1. The Workspace (Where blocks go)
    workspace_column = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    
    workspace_container = ft.Container(
        content=workspace_column,
        expand=True,
        bgcolor=ft.Colors.GREY_900,
        border_radius=15,
        padding=20,
        border=ft.border.all(1, ft.Colors.WHITE10)
    )

    # 2. The Log Console (To see output)
    log_column = ft.Column(scroll=ft.ScrollMode.ALWAYS, auto_scroll=True)
    
    def log_message(message, color=ft.Colors.WHITE):
        log_column.controls.append(ft.Text(f"> {message}", color=color, font_family="Consolas"))
        log_column.update()

    log_container = ft.Container(
        content=log_column,
        height=150,
        bgcolor=ft.Colors.BLACK,
        border_radius=10,
        padding=10,
        margin=ft.margin.only(top=10)
    )

    # 3. Helpers to manage blocks
    def remove_block(block_instance):
        workspace_column.controls.remove(block_instance)
        workspace_column.update()

    def add_block(func_type):
        block = FunctionBlock(func_type, remove_block)
        workspace_column.controls.append(block)
        workspace_column.update()

    # 4. The Runner Logic
    def run_preset(e):
        log_column.controls.clear()
        log_message("--- STARTED PRESET EXECUTION ---", ft.Colors.CYAN)
        
        # Loop through visual blocks
        for control in workspace_column.controls:
            if isinstance(control, FunctionBlock):
                config = control.get_configuration()
                
                # Dispatch execution
                try:
                    if config['type'] == "Buy Items":
                        qty = int(config.get('quantity', 0))
                        item = config.get('item_name', "Unknown")
                        execute_buy_items(item, qty, log_message)
                        
                    elif config['type'] == "Remove Orders":
                        oid = config.get('order_id', "Unknown")
                        execute_remove_orders(oid, log_message)
                        
                    elif config['type'] == "Check Prices":
                        item = config.get('item_name', "Unknown")
                        execute_check_prices(item, log_message)
                except Exception as ex:
                    log_message(f"ERROR: {str(ex)}", ft.Colors.RED)
        
        log_message("--- EXECUTION FINISHED ---", ft.Colors.CYAN)

    # -- Layout Assembly --

    # Sidebar Buttons
    sidebar = ft.Column(
        width=200,
        controls=[
            ft.Text("Palette", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.ElevatedButton(
                "Buy Items", 
                icon=ft.Icons.ADD, 
                bgcolor=ft.Colors.INDIGO_600, 
                color=ft.Colors.WHITE,
                on_click=lambda _: add_block("Buy Items"),
                width=180
            ),
            ft.ElevatedButton(
                "Remove Orders", 
                icon=ft.Icons.ADD, 
                bgcolor=ft.Colors.RED_700, 
                color=ft.Colors.WHITE,
                on_click=lambda _: add_block("Remove Orders"),
                width=180
            ),
            ft.ElevatedButton(
                "Check Prices", 
                icon=ft.Icons.ADD, 
                bgcolor=ft.Colors.TEAL_600, 
                color=ft.Colors.WHITE,
                on_click=lambda _: add_block("Check Prices"),
                width=180
            ),
            ft.Container(height=20),
            ft.Divider(),
            ft.FloatingActionButton(
                text="RUN PRESET",
                icon=ft.Icons.PLAY_ARROW,
                bgcolor=ft.Colors.GREEN,
                width=180,
                on_click=run_preset
            )
        ]
    )

    # Main Layout
    layout = ft.Row(
        controls=[
            sidebar,
            ft.VerticalDivider(width=1, color=ft.Colors.WHITE10),
            ft.Column(
                expand=True,
                controls=[
                    ft.Text("Workspace", size=20, weight=ft.FontWeight.BOLD),
                    workspace_container,
                    ft.Text("Console Log", size=14, color=ft.Colors.GREY_500),
                    log_container
                ]
            )
        ],
        expand=True
    )

    page.add(layout)

ft.app(target=main)