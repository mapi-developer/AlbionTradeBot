from ..core.point import Point


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
    def __init__(self, user_id: str, nickname: str, x: float = 0.0, y: float = 0.0, equipment: list[int] = [0]*10):
        super().__init__(user_id, nickname, x, y, equipment)
        self.location = ""
        self.inventory = {}