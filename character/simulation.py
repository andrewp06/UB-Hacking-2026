
import math
import pymunk
from dataclasses import dataclass

from shape import Shape
from joint import Joint


@dataclass
class SimulationResult:
    distance: float
    survival_time: float
    fell: bool


class Simulation:
    def __init__(self, shapes, joints, positions, radii,
                 motor_speeds, head, gravity=-981, duration=30.0):

        self.shapes = shapes
        self.joints = joints
        self.positions = positions
        self.radii = radii
        self.motor_speeds = motor_speeds
        self.head = head
        self.gravity = gravity
        self.duration = duration

        if not shapes:
            raise ValueError("At least one shape is required.")

        if any(shape.mass <= 0 for shape in shapes):
            raise ValueError("Shape masses must be positive.")

    def run(self):
        # Create a fresh physics world
        space = pymunk.Space()
        space.gravity = (0, self.gravity)

        # Create the ground at y = 0
        ground = pymunk.Segment(
            space.static_body,
            (-10000, 0),
            (10000, 0),
            5
        )

        ground.friction = 1.0
        space.add(ground)

        bodies = {}

        # Create physics bodies from Shape objects
        for i, shape in enumerate(self.shapes):
            mass = shape.get_mass()
            radius = self.radii[i]

            moment = pymunk.moment_for_circle(
                mass, 0, radius
            )

            body = pymunk.Body(mass, moment)
            body.position = self.positions[i]

            hitbox = pymunk.Circle(body, radius)
            hitbox.friction = 1.0

            # Prevent alien parts colliding with each other.
            hitbox.filter = pymunk.ShapeFilter(group=1)

            space.add(body, hitbox)

            # Use identity because dataclasses are unhashable
            bodies[id(shape)] = body

        # Create Pymunk joints
        for i, joint in enumerate(self.joints):
            parent = joint.get_shape_Parent()
            child = joint.get_shape_Child()

            if id(parent) not in bodies or id(child) not in bodies:
                raise ValueError(
                    "A joint references a shape not in this simulation."
                )

            body_a = bodies[id(parent)]
            body_b = bodies[id(child)]

            # Temporary pivot at the midpoint
            anchor = (
                (body_a.position.x + body_b.position.x) / 2,
                (body_a.position.y + body_b.position.y) / 2
            )

            pivot = pymunk.PivotJoint(
                body_a, body_b, anchor
            )

            limit = pymunk.RotaryLimitJoint(
                body_a,
                body_b,
                math.radians(joint.get_min_angle()),
                math.radians(joint.get_max_angle())
            )

            motor = pymunk.SimpleMotor(
                body_a,
                body_b,
                self.motor_speeds[i]
            )

            motor.max_force = 100000

            space.add(pivot, limit, motor)

        # First shape is considered the torso
        head_body = bodies[id(self.head)]
        head_index = next(
    i for i, shape in enumerate(self.shapes)
    if shape is self.head
)
        head_radius = self.radii[head_index]

        start_x = self.head.position.x
        max_distance = 0.0

        dt = 1 / 120
        elapsed = 0.0
        fell = False

        # Run simulation without rendering
        for _ in range(int(self.duration / dt)):
            space.step(dt)
            elapsed += dt

            distance = self.head.position.x - start_x
            max_distance = max(max_distance, distance)

            # Torso touching the ground means failure
            if head_body.position.y <= head_radius + 5:
                fell = True
                break

        return SimulationResult(
            distance=max_distance,
            survival_time=elapsed,
            fell=fell
        )
