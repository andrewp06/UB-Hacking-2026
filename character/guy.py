from .head import Head
from .shape import Shape
from .joint import Joint

class Guy:
    def __init__(self, head:Head):
        self.__head = head
        self.__shapes = []
        self.__joints = []

    def add_shape(self, shape:Shape):
        self.__shapes.append(shape)

    def remove_shape(self, shape:Shape):
        self.__shapes.remove(shape)

    def add_joint(self, joint:Joint):
        self.__joints.append(joint)

    def remove_joint(self, joint:Joint):
        self.__joints.remove(joint)


    def get_head(self):
        return self.__head

    def get_shapes(self):
        return self.__shapes

    def get_joints(self):
        return self.__joints