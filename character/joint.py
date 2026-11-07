
from dataclasses import dataclass
from shape import Shape


@dataclass
class Joint:
    ParentShape: Shape
    ChildShape: Shape
    maxAngle: int
    minAngle: int

    def set_max_angle(self, angle: int):
        self.maxAngle = angle

    def set_min_angle(self, angle: int):
        self.minAngle = angle

    def get_max_angle(self):
        return self.maxAngle

    def get_min_angle(self):
        return self.minAngle

    def get_shape_Parent(self):
        return self.ParentShape

    def get_shape_Child(self):
        return self.ChildShape
