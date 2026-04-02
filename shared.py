from dataclasses import dataclass

@dataclass
class Obstacle:
  obstacle_id: int
  pos: list[float]    # [x, y] center in meters
  dim: list[float]    # circle: [r], box/triangle: [dx, dy, theta]


@dataclass
class Circle(Obstacle):
  def __init__(self, obstacle_id: int, pos: list[float], radius: float = 0.35):
    super().__init__(obstacle_id, pos, [radius])


@dataclass
class Box(Obstacle):
  def __init__(self, obstacle_id: int, pos: list[float], dx: float = 0.70, dy: float = 0.50, theta: float = 0.0):
    super().__init__(obstacle_id, pos, [dx, dy, theta])


@dataclass
class Triangle(Obstacle):
  def __init__(self, obstacle_id: int, pos: list[float], dx: float = 0.70, dy: float = 0.50, theta: float = 0.0):
    super().__init__(obstacle_id, pos, [dx, dy, theta])