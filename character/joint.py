from shape import Shape

class Joint:
    def __init__(self, shapeA:Shape, shapeB:Shape, maxAngle:int, minAngle:int):
        self.shapeA = shapeA
        self.shapeB = shapeB
        self.maxAngle = maxAngle
        self.minAngle = minAngle