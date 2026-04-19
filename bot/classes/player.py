from ..core.point import Point
from ..classes.location import Location


class Equipment():
    def __init__(self, parent, items: list[int] = [0]*10):
        self._parent = parent
        self.main_hand = items[0]
        self.off_hand = items[1]
        self.head_armor = items[2]
        self.chest_armor = items[3]
        self.foot_armor = items[4]
        self.bag = items[5]
        self.cape = items[6]
        self.mount = items[7]
        self.potion = items[8]
        self.food = items[9]

    def __repr__(self):
        return f"[{self.main_hand}, {self.off_hand}, {self.head_armor}, {self.chest_armor}, {self.foot_armor}, {self.bag}, {self.cape}, {self.mount}, {self.potion}, {self.food}]"
    
    def to_list(self) -> list:
        return [
            self.main_hand,
            self.off_hand,
            self.head_armor,
            self.chest_armor,
            self.foot_armor,
            self.bag,
            self.cape,
            self.mount,
            self.potion,
            self.food,
        ]

    def clear(self):
        self.main_hand = 0
        self.off_hand = 0
        self.head_armor = 0
        self.chest_armor = 0
        self.foot_armor = 0
        self.bag = 0
        self.cape = 0
        self.mount = 0
        self.potion = 0
        self.food = 0

    def from_list(self, equipment: list[int]):
        self.main_hand = equipment[0]
        self.off_hand = equipment[1]
        self.head_armor = equipment[2]
        self.chest_armor = equipment[3]
        self.foot_armor = equipment[4]
        self.bag = equipment[5]
        self.cape = equipment[6]
        self.mount = equipment[7]
        self.potion = equipment[8]
        self.food = equipment[9]

class Player:
    def __init__(self, user_id: str, nickname: str, x: float = 0.0, y: float = 0.0, equipment: list[int] = [0]*10):
        self.user_id = user_id
        self.nickname = nickname
        self.position = Point(self, x, y)
        self.equipment = Equipment(self, equipment if equipment else [0]*10)


class LocalPlayer(Player):
    def __init__(self, user_id: str = "", nickname: str = "", x: float = 0.0, y: float = 0.0, equipment: list[int] = [0]*10):
        super().__init__(user_id, nickname, x, y, equipment)
        self.silver_balance = 0
        self.location = Location()
        self.inventory = {}

    def clear_inventory(self):
        self.inventory.clear()

    def get_inventory(self) -> dict:
        return self.inventory

    def on_new_item(self, local_index: int, item_id: int, is_inventory: bool = False):
        if is_inventory: 
            self.inventory[local_index] = item_id

    def on_silver_changed(self, value: int):
        self.silver_balance = value

    def on_position_changed(self, position: list[float]):
        self.position.x, self.position.y = position[0], position[1]

    def on_nickname_changed(self, nickname: str, local_id: int):
        self.nickname = nickname
        self.user_id = local_id

    def on_location_changed(self, location_id: str, location_type: str, location_name: str):
        self.location.location_id = location_id
        self.location.location_type = location_type
        self.location.location_name = location_name