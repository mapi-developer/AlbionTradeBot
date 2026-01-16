class Point:
    def __init__(self, parent, x: float, y: float):
        self._parent = parent
        self.x = x
        self.y = y

    def __add__(self, other):
        if isinstance(other, (list, tuple)):
            if len(other) != 2:
                raise ValueError("Can only add a list/tuple of length 2")
            return [self.x + other[0], self.y + other[1]]
        
        elif isinstance(other, Point):
            return [self.x + other.x, self.y + other.y]
            
        return NotImplemented

    def __repr__(self):
        return f"[{self.x}, {self.y}]"
    
    def to_list(self) -> list:
        return [self.x, self.y]