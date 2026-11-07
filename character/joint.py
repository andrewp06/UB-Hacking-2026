from shape import Shape

class Joint:
    def __init__(self, shapeA:Shape, shapeB:Shape, maxAngle:int, minAngle:int):
        self.__shapeA = shapeA
        self.__shapeB = shapeB
        self.__maxAngle = maxAngle
        self.__minAngle = minAngle

    def set_max_angle(self, angle:int):
        self.__maxAngle = angle

    def set_min_angle(self, angle:int):
        self.__minAngle = angle

    def get_max_angle(self):
        return self.__maxAngle

    def get_min_angle(self):
        return self.__minAngle

    def get_shape_a(self):
        return self.__shapeA
    
    def get_shape_b(self):
        return self.__shapeB