from .head import Head
from .shape import Shape
from .joint import Joint

class Guy:
    """A user-built alien: one head, body parts, and connecting joints."""

    def __init__(self, head: Head):
        if not isinstance(head, Head):
            raise TypeError("head must be a Head (for example, Circle).")
        self.__head = head
        self.__shapes = [head]
        self.__joints = []

    def add_shape(self, shape: Shape) -> None:
        if not isinstance(shape, Shape):
            raise TypeError("shape must inherit from Shape.")
        if any(part is shape for part in self.__shapes):
            raise ValueError("That shape is already in the alien.")
        self.__shapes.append(shape)

    def remove_shape(self, shape: Shape) -> None:
        if shape is self.__head:
            raise ValueError("The head cannot be removed.")
        if not any(part is shape for part in self.__shapes):
            raise ValueError("Shape is not in the alien.")
        self.__joints = [
            joint for joint in self.__joints
            if joint.get_shape_Parent() is not shape
            and joint.get_shape_Child() is not shape
        ]
        self.__shapes = [part for part in self.__shapes if part is not shape]

    def add_joint(self, joint: Joint) -> None:
        if not isinstance(joint, Joint):
            raise TypeError("joint must be a Joint.")
        parent = joint.get_shape_Parent()
        child = joint.get_shape_Child()
        if parent is child:
            raise ValueError("A joint cannot connect a part to itself.")
        if not any(part is parent for part in self.__shapes):
            raise ValueError("Joint parent is not in the alien.")
        if not any(part is child for part in self.__shapes):
            raise ValueError("Joint child is not in the alien.")
        if any(old is joint for old in self.__joints):
            raise ValueError("That joint is already in the alien.")
        self.__joints.append(joint)

    def remove_joint(self, joint: Joint) -> None:
        if not any(old is joint for old in self.__joints):
            raise ValueError("Joint is not in the alien.")
        self.__joints = [old for old in self.__joints if old is not joint]

    def get_head(self) -> Head:
        return self.__head

    def get_shapes(self) -> list[Shape]:
        return self.__shapes.copy()

    def get_joints(self) -> list[Joint]:
        return self.__joints.copy()
