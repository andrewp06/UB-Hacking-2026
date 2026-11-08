from .head import Head
from .shape import Shape
from .joint import Joint

class Guy:
    def __init__(self, head:Head):
        self.__head = head
        self.__shapes = []
        self.__joints = []

    def add_shape(self, parentShape:Shape, newShape:Shape, min_angle:int = 0, max_angle:int = 360):
        if parentShape in self.__shapes and newShape not in self.__shapes:  
            self.__shapes.append(newShape)
            self.__joints.append(Joint(parentShape, newShape), max_angle, min_angle)

    def remove_shape(self, shape:Shape):
        self.__shapes.remove(shape)
        for joint in self.__joints:
            if joint.has_shape(shape):
                self.__joints.remove(joint)

    def get_head(self):
        return self.__head

    def get_shapes(self):
        return self.__shapes

    def get_joints(self):
        return self.__joints