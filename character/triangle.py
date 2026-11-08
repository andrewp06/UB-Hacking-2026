from .head import Head

class Triangle(Head):
    def __init__(self, mass: float, height: float):
        super().__init__(mass)
        self.__height = height

    def get_height(self):
        return self.__height

    def set_height(self, radius: float):
        self.__height = radius