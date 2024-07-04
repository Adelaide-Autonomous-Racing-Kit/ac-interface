from dataclasses import dataclass


@dataclass
class Point:
    """
    A class representing a point in 2D space
    """

    x: int
    y: int

    def __add__(self, point):
        x = self.x + point.x
        y = self.y + point.y
        return Point(x, y)

    def __repr__(self) -> str:
        return f"(x={self.x}, y={self.y})"
