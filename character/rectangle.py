from shape import Shape

class Rectangle:
    def __init__ (self, length:float, width:float):
        self.__width = width
        self.__length = length

    def get_width(self):
        return self.__width

    def get_length(self):
        return self.__length

    def set_width(self, width:float):
        self.__width = width

    def set_length(self, length:float):
        self.__length = length