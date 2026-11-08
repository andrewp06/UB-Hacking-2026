import math
from dataclasses import dataclass

import pymunk

from .circle import Circle
from .rectangle import Rectangle
from .guy import Guy
from .head import Head


@dataclass
class SimulationResult:
    distance: float
    survival_time: float
    fell: bool


class Simulation:
    def __init__(
        self,
        guy: Guy,
        positions: list[tuple[float, float]],
        motor_speeds: list[float] | None = None,
        joint_anchors: list[tuple[float, float]] | None = None,
        gravity: float = -981.0,
        duration: float = 10.0,
        motor_max_force: float = 100000.0,
    ):
        if not isinstance(guy, Guy):
            raise TypeError("guy must be a Guy object")
        self.guy = guy
        self.shapes = guy.get_shapes()
        self.joints = guy.get_joints()
        self.head = guy.get_head()
        self.positions = list(positions)
        self.motor_speeds = (
            [0.0] * len(self.joints)
            if motor_speeds is None else list(motor_speeds)
        )
        self.joint_anchors = (
            None if joint_anchors is None else list(joint_anchors)
        )
        self.gravity = float(gravity)
        self.duration = float(duration)
        self.motor_max_force = float(motor_max_force)

        if not isinstance(self.head,Head ):
            raise TypeError("The head must be a Circle")
        if len(self.positions) != len(self.shapes):
            raise ValueError("Provide one position for each shape")
        if len(self.motor_speeds) != len(self.joints):
            raise ValueError("Provide one motor speed for each joint")
        if self.joint_anchors is not None and len(self.joint_anchors) != len(self.joints):
            raise ValueError("Provide one anchor for each joint")
        if len({id(part) for part in self.shapes}) != len(self.shapes):
            raise ValueError("Duplicate shapes are not allowed")
        for number in (self.gravity, self.duration, self.motor_max_force):
            if not math.isfinite(number):
                raise ValueError("Physics settings must be finite")
        if self.duration <= 0 or self.motor_max_force <= 0:
            raise ValueError("Duration and motor_max_force must be positive")
        for position in self.positions + (self.joint_anchors or []):
            if len(position) != 2 or not all(math.isfinite(float(v)) for v in position):
                raise ValueError("Positions and anchors must be finite (x, y) pairs")
        if not all(math.isfinite(float(s)) for s in self.motor_speeds):
            raise ValueError("Motor speeds must be finite")
        for part in self.shapes:
            if part.get_mass() <= 0:
                raise ValueError("Masses must be positive")
            if isinstance(part, Circle):
                if part.get_radius() <= 0:
                    raise ValueError("Circle radius must be positive")
            elif isinstance(part, Rectangle):
                if part.get_length() <= 0 or part.get_width() <= 0:
                    raise ValueError("Rectangle dimensions must be positive")
            else:
                raise TypeError("Only Circle and Rectangle are currently supported")
        for joint in self.joints:
            if joint.get_min_angle() > joint.get_max_angle():
                raise ValueError("Joint minimum angle exceeds maximum angle")

        self.reset()

    def reset(self):
        """Build a fresh Pymunk world, resetting time and torque commands."""
        self.space = pymunk.Space()
        self.space.gravity = (0, self.gravity)
        self.ground_radius = 5.0
        ground = pymunk.Segment(
            self.space.static_body, (-100000, 0), (100000, 0),
            self.ground_radius,
        )
        ground.friction = 1.2
        ground.collision_type = 1
        self.space.add(ground)

        self.bodies = {}
        self.hitboxes = {}
        self.limb_torques = {id(part): 0.0 for part in self.shapes}
        self.joint_torques = {id(joint): 0.0 for joint in self.joints}
        self.motors = []
        self.elapsed = 0.0
        self.distance = 0.0
        self.fell = False

        for part, position in zip(self.shapes, self.positions):
            mass = part.get_mass()
            if isinstance(part, Circle):
                radius = part.get_radius()
                inertia = pymunk.moment_for_circle(mass, 0, radius)
                body = pymunk.Body(mass, inertia)
                hitbox = pymunk.Circle(body, radius)
            else:
                size = (part.get_length(), part.get_width())
                inertia = pymunk.moment_for_box(mass, size)
                body = pymunk.Body(mass, inertia)
                hitbox = pymunk.Poly.create_box(body, size)
            body.position = position
            hitbox.friction = 1.0
            hitbox.elasticity = 0.0
            hitbox.filter = pymunk.ShapeFilter(group=1)
            if part is self.head:
                hitbox.collision_type = 2
            self.space.add(body, hitbox)
            self.bodies[id(part)] = body
            self.hitboxes[id(part)] = hitbox

        def head_ground_collision(arbiter, space, data):
            self.fell = True
            return True

        if hasattr(self.space, "on_collision"):
            self.space.on_collision(1, 2, begin=head_ground_collision)
        else:
            self.space.add_collision_handler(1, 2).begin = head_ground_collision

        for i, (joint, speed) in enumerate(zip(self.joints, self.motor_speeds)):
            parent = self.bodies[id(joint.get_shape_Parent())]
            child = self.bodies[id(joint.get_shape_Child())]
            if self.joint_anchors is None:
                anchor = (
                    (parent.position.x + child.position.x) / 2,
                    (parent.position.y + child.position.y) / 2,
                )
            else:
                anchor = self.joint_anchors[i]
            pivot = pymunk.PivotJoint(parent, child, anchor)
            limit = pymunk.RotaryLimitJoint(
                parent, child,
                math.radians(joint.get_min_angle()),
                math.radians(joint.get_max_angle()),
            )
            self.space.add(pivot, limit)
            # A zero-speed motor resists rotation, so omit it for torque control.
            if speed != 0:
                motor = pymunk.SimpleMotor(parent, child, speed)
                motor.max_force = self.motor_max_force
                self.space.add(motor)
                self.motors.append(motor)

        tracked_part = next(
            (part for part in self.shapes if part is not self.head), self.head
        )
        self.tracked = self.bodies[id(tracked_part)]
        self.start_x = self.tracked.position.x

    def set_limb_torque(self, limb, torque: float):
        """Set a persistent torque on a shape (+ is counterclockwise)."""
        if id(limb) not in self.bodies:
            raise ValueError("Limb is not part of this alien")
        if not math.isfinite(torque):
            raise ValueError("Torque must be finite")
        self.limb_torques[id(limb)] = float(torque)

    def set_joint_torque(self, joint, torque: float):
        """Set a persistent actuator torque on a joint's parent and child."""
        if not any(candidate is joint for candidate in self.joints):
            raise ValueError("Joint is not part of this alien")
        if not math.isfinite(torque):
            raise ValueError("Torque must be finite")
        self.joint_torques[id(joint)] = float(torque)

    def get_result(self) -> SimulationResult:
        return SimulationResult(self.distance, self.elapsed, self.fell)

    def step(self, dt: float) -> SimulationResult:
        """Advance exactly dt seconds, unless the head has already fallen."""
        if not math.isfinite(dt) or dt <= 0:
            raise ValueError("dt must be a positive finite number")
        if self.fell:
            return self.get_result()

        # Accumulate all torque contributions before stepping the world.
        for part in self.shapes:
            self.bodies[id(part)].torque = self.limb_torques[id(part)]
        for joint in self.joints:
            torque = self.joint_torques[id(joint)]
            parent = self.bodies[id(joint.get_shape_Parent())]
            child = self.bodies[id(joint.get_shape_Child())]
            parent.torque -= torque
            child.torque += torque

        self.space.step(dt)
        self.elapsed += dt
        self.distance = max(
            self.distance, self.tracked.position.x - self.start_x
        )
        return self.get_result()

    def run(self, steps=None, dt=1/120, render=False) -> SimulationResult:
        """Run up to steps * dt seconds. Defaults to self.duration / dt."""
        if not math.isfinite(dt) or dt <= 0:
            raise ValueError("dt must be a positive finite number")
        if steps is None:
            steps = math.ceil(self.duration / dt)
        if type(steps) is not int or steps < 0:
            raise ValueError("steps must be a nonnegative integer")

        pygame = None
        screen = clock = font = None
        if render:
            import pygame as pygame_module
            pygame = pygame_module
            pygame.init()
            screen = pygame.display.set_mode((1000, 650))
            pygame.display.set_caption("Alien Physics Simulation")
            clock = pygame.time.Clock()
            font = pygame.font.Font(None, 25)

        def draw():
            if pygame is None:
                return
            screen.fill((23, 29, 42))
            width, height = screen.get_size()
            floor_y = height - 85
            camera_x = self.tracked.position.x - width * 0.4

            def screen_point(pos):
                return (int(pos.x - camera_x), int(floor_y - pos.y))

            pygame.draw.line(
                screen, (165, 180, 198),
                (0, floor_y + self.ground_radius),
                (width, floor_y + self.ground_radius), 10,
            )
            for constraint in self.space.constraints:
                if isinstance(constraint, pymunk.PivotJoint):
                    pos = constraint.a.local_to_world(constraint.anchor_a)
                    pygame.draw.circle(
                        screen, (255, 185, 70), screen_point(pos), 5
                    )
            for part in self.shapes:
                body = self.bodies[id(part)]
                hitbox = self.hitboxes[id(part)]
                color = (240, 99, 99) if part is self.head else (85, 185, 230)
                if isinstance(hitbox, pymunk.Circle):
                    pygame.draw.circle(
                        screen, color, screen_point(body.position),
                        max(1, round(hitbox.radius)),
                    )
                else:
                    points = [
                        screen_point(body.local_to_world(vertex))
                        for vertex in hitbox.get_vertices()
                    ]
                    pygame.draw.polygon(screen, color, points)
                    pygame.draw.polygon(screen, (240, 240, 240), points, 2)
            stats = (
                f"Time: {self.elapsed:.2f}s   Distance: {self.distance:.1f} "
                f"Head hit ground: {self.fell}"
            )
            screen.blit(font.render(stats, True, (240, 240, 245)), (15, 15))
            pygame.display.flip()

        try:
            frame_time = 0.0
            if pygame is not None:
                draw()
            for _ in range(steps):
                if pygame is not None:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            return self.get_result()
                        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                            return self.get_result()
                if self.fell:
                    break
                self.step(dt)
                frame_time += dt
                if pygame is not None and (frame_time >= 1 / 60 or self.fell):
                    draw()
                    clock.tick(60)
                    frame_time = 0.0
            if pygame is not None:
                draw()
                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            waiting = False
                        elif event.type == pygame.KEYDOWN and event.key in (
                            pygame.K_ESCAPE, pygame.K_SPACE
                        ):
                            waiting = False
                    clock.tick(30)
        finally:
            if pygame is not None:
                pygame.quit()
        return self.get_result()


if __name__ == "__main__":
    from .joint import Joint

    head = Circle(mass=1.0, radius=13.0)
    torso = Rectangle(mass=5.0, length=48.0, width=24.0)
    left_leg = Rectangle(mass=2.0, length=12.0, width=54.0)
    right_leg = Rectangle(mass=2.0, length=12.0, width=54.0)

    alien = Guy(head)
    for part in (torso, left_leg, right_leg):
        alien.add_shape(part)
    neck = Joint(torso, head, 20, -20)
    left_hip = Joint(torso, left_leg, 55, -55)
    right_hip = Joint(torso, right_leg, 55, -55)
    for joint in (neck, left_hip, right_hip):
        alien.add_joint(joint)

    trial = Simulation(
        guy=alien,
        positions=[(0, 124), (0, 86), (-17, 47), (17, 47)],
        joint_anchors=[(0, 105), (-17, 74), (17, 74)],
    )
    trial.set_joint_torque(left_hip, 250)
    trial.set_joint_torque(right_hip, 2000)
    print(trial.run(steps=1200, dt=1 / 120, render=True))