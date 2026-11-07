from head import Head

class Circle(Head):

    def __init__(self, radius:float):
        self.__radius = radius

    def get_radius(self):
        return self.__radius

    def set_radius(self, radius:float):
        self.__radius = radius