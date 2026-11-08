
import math
from dataclasses import dataclass

import pymunk

from .circle import Circle
from .rectangle import Rectangle
from .guy import Guy

@dataclass
class SimulationResult:
    distance: float
    survival_time: float
    fell: bool  # True only if the HEAD contacted the ground


class Simulation:
    def __init__(
        self,
        guy: Guy,
        positions: list[tuple[float, float]],
        motor_speeds: list[float],
        joint_anchors: list[tuple[float, float]] | None = None,
        gravity: float = -981.0,
        duration: float = 10.0,
        motor_max_force: float = 100000.0,
    ):
        """Positions match guy.get_shapes() order; speeds/anchors match joints.

        joint_anchors are WORLD coordinates. When omitted, each joint uses
        the midpoint of its two body centers (a simple fallback).
        """
        if not isinstance(guy, Guy):
            raise TypeError("guy must be an instance of Guy.")
        self.guy = guy
        self.shapes = guy.get_shapes()
        self.joints = guy.get_joints()
        self.positions = list(positions)
        self.motor_speeds = list(motor_speeds)
        self.joint_anchors = None if joint_anchors is None else list(joint_anchors)
        self.gravity = float(gravity)
        self.duration = float(duration)
        self.motor_max_force = float(motor_max_force)

        if len(self.positions) != len(self.shapes):
            raise ValueError("Supply one starting position per shape.")
        if len(self.motor_speeds) != len(self.joints):
            raise ValueError("Supply one motor speed per joint.")
        if self.joint_anchors is not None and len(self.joint_anchors) != len(self.joints):
            raise ValueError("Supply one anchor position per joint.")
        if self.duration <= 0 or not math.isfinite(self.duration):
            raise ValueError("Duration must be a positive finite number.")
        if self.motor_max_force <= 0 or not math.isfinite(self.motor_max_force):
            raise ValueError("Motor max force must be positive and finite.")
        if not math.isfinite(self.gravity):
            raise ValueError("Gravity must be finite.")
        if not all(math.isfinite(float(v)) for point in self.positions for v in point):
            raise ValueError("Positions must contain finite coordinates.")
        if not all(math.isfinite(float(speed)) for speed in self.motor_speeds):
            raise ValueError("Motor speeds must be finite.")
        if self.joint_anchors is not None and not all(
            math.isfinite(float(v)) for point in self.joint_anchors for v in point
        ):
            raise ValueError("Joint anchors must contain finite coordinates.")
        if not isinstance(guy.get_head(), Circle):
            raise TypeError("The current simulation requires a circular head (Circle).")

    def run(self, render: bool = False) -> SimulationResult:
        """Build a fresh world and simulate. render=False opens no window."""
        space = pymunk.Space()
        space.gravity = (0, self.gravity)

        ground_radius = 5.0
        ground = pymunk.Segment(
            space.static_body, (-10000, 0), (10000, 0), ground_radius
        )
        ground.friction = 1.2
        ground.collision_type = 1
        space.add(ground)

        # Shape dataclasses are unhashable: use object IDs as dictionary keys.
        bodies = {}
        hitboxes = {}
        for part, position in zip(self.shapes, self.positions):
            mass = part.get_mass()
            if mass <= 0:
                raise ValueError("All body masses must be positive.")

            if isinstance(part, Circle):
                radius = part.get_radius()
                moment = pymunk.moment_for_circle(mass, 0, radius)
                body = pymunk.Body(mass, moment)
                hitbox = pymunk.Circle(body, radius)
            elif isinstance(part, Rectangle):
                # length is horizontal (x); width is vertical (y).
                dimensions = (part.get_length(), part.get_width())
                moment = pymunk.moment_for_box(mass, dimensions)
                body = pymunk.Body(mass, moment)
                hitbox = pymunk.Poly.create_box(body, dimensions)
            else:
                raise TypeError(
                    f"Unsupported shape type: {type(part).__name__}. "
                    "Use Circle or Rectangle."
                )

            body.position = position
            hitbox.friction = 1.0
            hitbox.elasticity = 0.0
            # Suppress internal alien-vs-alien collisions, not ground collisions.
            hitbox.filter = pymunk.ShapeFilter(group=1)
            space.add(body, hitbox)
            bodies[id(part)] = body
            hitboxes[id(part)] = hitbox

        head = self.guy.get_head()
        head_body = bodies[id(head)]
        head_hitbox = hitboxes[id(head)]
        head_hitbox.collision_type = 2

        # Register a real collision callback for head vs. ground.
        # Pymunk 7 uses on_collision; Pymunk 6 uses add_collision_handler.
        head_touched_ground = False

        def on_head_ground_contact(arbiter, space, data):
            nonlocal head_touched_ground
            head_touched_ground = True
            return True

        if hasattr(space, "on_collision"):
            space.on_collision(1, 2, begin=on_head_ground_contact)
        else:
            handler = space.add_collision_handler(1, 2)
            handler.begin = on_head_ground_contact

        for index, (joint, speed) in enumerate(zip(self.joints, self.motor_speeds)):
            parent = bodies[id(joint.get_shape_Parent())]
            child = bodies[id(joint.get_shape_Child())]
            if self.joint_anchors is None:
                anchor = (
                    (parent.position.x + child.position.x) / 2,
                    (parent.position.y + child.position.y) / 2,
                )
            else:
                anchor = self.joint_anchors[index]

            pivot = pymunk.PivotJoint(parent, child, anchor)
            limit = pymunk.RotaryLimitJoint(
                parent, child,
                math.radians(joint.get_min_angle()),
                math.radians(joint.get_max_angle()),
            )
            motor = pymunk.SimpleMotor(parent, child, speed)
            motor.max_force = self.motor_max_force
            space.add(pivot, limit, motor)

        # Track the first non-head body, falling back to head for a head-only alien.
        tracking_part = next(
            (part for part in self.shapes if part is not head), head
        )
        tracking_body = bodies[id(tracking_part)]
        start_x = tracking_body.position.x
        distance = 0.0
        elapsed = 0.0
        fell = False
        dt = 1.0 / 120.0

        pygame = None
        screen = clock = font = None
        if render:
            import pygame as pygame_module
            pygame = pygame_module
            pygame.init()
            screen = pygame.display.set_mode((1000, 650))
            pygame.display.set_caption("Alien Physics Simulation")
            clock = pygame.time.Clock()
            font = pygame.font.SysFont(None, 25)

        def draw():
            if pygame is None:
                return
            screen.fill((23, 29, 42))
            width, height = screen.get_size()
            floor_y = height - 85
            camera_x = tracking_body.position.x - width * 0.4

            def screen_point(p):
                return (int(p.x - camera_x), int(floor_y - p.y))

            pygame.draw.line(
                screen, (160, 177, 193),
                (0, floor_y + ground_radius),
                (width, floor_y + ground_radius), 10,
            )
            # Render actual pivot anchors (not center-to-center lines).
            for constraint in space.constraints:
                if isinstance(constraint, pymunk.PivotJoint):
                    p = constraint.a.local_to_world(constraint.anchor_a)
                    pygame.draw.circle(screen, (255, 190, 85), screen_point(p), 5)

            for part in self.shapes:
                body = bodies[id(part)]
                hitbox = hitboxes[id(part)]
                color = (242, 105, 105) if part is head else (83, 185, 228)
                if isinstance(hitbox, pymunk.Circle):
                    center = screen_point(body.local_to_world(hitbox.offset))
                    pygame.draw.circle(screen, color, center, max(1, int(hitbox.radius)))
                    pygame.draw.circle(screen, (235, 240, 247), center, max(1, int(hitbox.radius)), 2)
                    endpoint = (
                        center[0] + int(math.cos(body.angle) * hitbox.radius),
                        center[1] - int(math.sin(body.angle) * hitbox.radius),
                    )
                    pygame.draw.line(screen, (35, 55, 70), center, endpoint, 2)
                else:
                    points = [screen_point(body.local_to_world(v)) for v in hitbox.get_vertices()]
                    pygame.draw.polygon(screen, color, points)
                    pygame.draw.polygon(screen, (235, 240, 247), points, 2)

            text = (
                f"Time: {elapsed:.2f}s    Distance: {distance:.1f} units    "
                f"Head hit ground: {fell}"
            )
            screen.blit(font.render(text, True, (240, 240, 245)), (15, 15))
            screen.blit(
                font.render("Red = head   |   Space / Esc = close after trial", True, (190, 200, 220)),
                (15, 43),
            )
            pygame.display.flip()

        keep_running = True
        try:
            steps = math.ceil(self.duration / dt)
            for step in range(steps):
                if pygame is not None:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            keep_running = False
                        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                            keep_running = False
                    if not keep_running:
                        break

                space.step(dt)
                elapsed = min((step + 1) * dt, self.duration)
                distance = max(distance, tracking_body.position.x - start_x)
                # Backup flat-ground check for touching at initialization.
                # Callback is the primary check for actual collisions.
                fell = head_touched_ground or (
                    head_body.position.y <= head.get_radius() + ground_radius
                )

                if pygame is not None and (step % 2 == 0 or fell):
                    draw()
                    clock.tick(60)
                if fell:
                    break

            if pygame is not None and keep_running:
                draw()
                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            waiting = False
                        elif event.type == pygame.KEYDOWN and event.key in (
                            pygame.K_SPACE, pygame.K_ESCAPE
                        ):
                            waiting = False
                    clock.tick(30)
        finally:
            if pygame is not None:
                pygame.quit()

        return SimulationResult(distance, elapsed, fell)


# if __name__ == "__main__":
#     # Example: head + torso + two legs.
#     # Start with these positions and anchors, then adapt to the GUI builder.
#     from .joint import Joint

#     head = Circle(mass=1.0, radius=13.0)
#     torso = Rectangle(mass=5.0, length=48.0, width=24.0)
#     left_leg = Rectangle(mass=2.0, length=12.0, width=54.0)
#     right_leg = Rectangle(mass=2.0, length=12.0, width=54.0)

#     alien = Guy(head)
#     for part in (torso, left_leg, right_leg):
#         alien.add_shape(part)

#     alien.add_joint(Joint(torso, head, 20, -20))
#     alien.add_joint(Joint(torso, left_leg, 55, -55))
#     alien.add_joint(Joint(torso, right_leg, 55, -55))

#     trial = Simulation(
#         guy=alien,
#         # Guy stores the head first, followed by added parts.
#         positions=[(0, 124), (0, 86), (-17, 47), (17, 47)],
#         motor_speeds=[0.0, 3.0, -3.0],
#         joint_anchors=[(0, 105), (-17, 74), (17, 74)],
#         duration=10.0,
#     )
#     print(trial.run(render=True))
