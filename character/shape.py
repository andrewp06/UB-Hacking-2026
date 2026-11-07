
from dataclasses import dataclass


@dataclass
class Shape:
    mass: float

    def get_hitbox(self):
        print("Warning, get_hitbox has not been overridden")
        return None

    def get_mass(self):
        return self.mass

    def set_mass(self, mass: float):
        self.mass = mass
