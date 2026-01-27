from ..core import InputSender, WindowCapture
from .settings import SettingsHandler


class ChestHandler(InputSender):
    def __init__(self, capture: WindowCapture, settings: SettingsHandler):
        super().__init__()
        self.settings = settings
        self.mouse_positions = self.settings.MOUSE_POSITIONS[capture.get_window_resolution()]["chest"]

    def take_mount(self):
        self.click(self.mouse_positions["bank_tab"])
        self.sleep(.2)
        self.click(self.mouse_positions["bank_tab_1"])
        self.right_click_with_key(self.mouse_positions["bank_tab_slot_1"], "shift")
        self.sleep(.2)

    def stash_mount(self):
        self.click(self.mouse_positions["bank_tab"])
        self.sleep(.2)
        self.click(self.mouse_positions["bank_tab_1"])
        self.drag(self.mouse_positions["inventory_mount"], self.mouse_positions["bank_tab_slot_1"], .2)
        self.sleep(.2)

    def take_items_from_tab(self):
        self.click(self.mouse_positions["bank_tab"])
        self.sleep(.2)
        self.click(self.mouse_positions["bank_tab_2"])
        self.sleep(.5)
        self.click(self.mouse_positions["bank_tab_move_all"])
        self.sleep(.6)
        self.click(self.mouse_positions["bank_tab_move_all"])
        self.sleep(.6)
        self.click(self.mouse_positions["bank_tab_move_all_to_inventory"])
        self.sleep(.2)
        self.click(self.mouse_positions["bank_tab_many_items_okay"])
        self.click(self.mouse_positions["bank_tab_sort"])
        self.sleep(.2)
        self.press("esc")

    def stash_item_into_tab(self):
        self.click(self.mouse_positions["bank_tab"])
        self.sleep(.2)
        self.click(self.mouse_positions["bank_tab_3"])
        self.sleep(.5)
        self.click(self.mouse_positions["bank_tab_move_all"])
        self.sleep(.6)
        self.click(self.mouse_positions["bank_tab_move_all"])
        self.sleep(.6)
        self.click(self.mouse_positions["bank_tab_move_all_from_inventory"])
        self.sleep(.2)
        self.click(self.mouse_positions["bank_tab_sort"])
        self.sleep(.2)

    def from_tab_to_tab(self):
        self.click(self.mouse_positions["bank_tab"])
        self.sleep(.2)
        self.click(self.mouse_positions["bank_tab_3"])
        self.click(self.mouse_positions["extend_second_tab"])
        self.click(self.mouse_positions["bank_second_tab"])
        self.sleep(.2)
        self.click(self.mouse_positions["bank_second_tab_2"])
        self.click(self.mouse_positions["bank_tab_move_all"])
        self.sleep(.5)
        self.click(self.mouse_positions["bank_tab_move_all"])
        self.click(self.mouse_positions["bank_tab_move_all_to_tab"])
        self.click(self.mouse_positions["close_second_tab"])
        self.press("esc")
        
        