from .shape import Shape

class Rectangle(Shape):
    """Rectangular body part with a mass, length, and width."""

    def __init__(self, mass: float, length: float, width: float):
        if mass <= 0:
            raise ValueError("Rectangle mass must be positive.")
        super().__init__(mass)
        self.set_length(length)
        self.set_width(width)

    def get_width(self) -> float:
        return self.__width

    def get_length(self) -> float:
        return self.__length

    def set_width(self, width: float) -> None:
        if width <= 0:
            raise ValueError("Rectangle width must be positive.")
        self.__width = float(width)

    def set_length(self, length: float) -> None:
        if length <= 0:
            raise ValueError("Rectangle length must be positive.")
        self.__length = float(length)

    def get_hitbox(self):
        # Length is the horizontal x size; width is the vertical y size.
        return ("rectangle", self.__length, self.__width)
