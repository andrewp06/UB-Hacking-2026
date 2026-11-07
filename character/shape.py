class Shape:
    def __init__(self, mass:float):
        self.__mass = mass

    def get_hitbox():
        print("Warning, getHitBox has not been overriden")

    def get_mass(self):
        return self.__mass

    def set_mass(self, mass:float):
        self.__mass = mass
