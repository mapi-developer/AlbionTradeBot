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

    def on_silver_changed(self, value: int):
        self.silver_balance = value

    def on_position_changed(self, position: list[float]):
        self.position.x, self.position.y = position[0], position[1]

    def on_nickname_changed(self, nickname: str):
        self.nickname = nickname

    def on_location_changed(self, location_id: str, location_type: str, location_name: str):
        self.location.location_id = location_id
        self.location.location_type = location_type
        self.location.location_name = location_name