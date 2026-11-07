from head import Head
from shape import Shape

class Guy:
    def __init__(self, head):
        self.__head = head
        self.__shapes = []

    def add_shape(self, shape: Shape):
        self.__shapes.append(shape)

    def remove_shape(self, shape:Shape):
        self.__shapes.remove(shape)

    def get_head(self):
        return self.__head
    