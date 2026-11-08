

import math
from dataclasses import dataclass

from character.circle import Circle
from character.rectangle import Rectangle
from character.guy import Guy
from character.joint import Joint


# Must match the dimensions, centers and pin offsets in character_creation.py.
# "leg" is a sprite, so its physics hitbox is currently a 120x120 box.
PARTS = {
    "circle_body": {"center": (80, 80), "size": (160, 160),
                    "pins": [(-31, -54), (31, -54), (-62, 0),
                             (62, 0), (-31, 54), (31, 54)]},
    "rect_limb": {"center": (25, 60), "size": (50, 120),
                  "pins": [(0, -50), (0, 50)]},
    "leg": {"center": (60, 60), "size": (120, 120),
            "pins": [(0, -50), (0, 50)]},
}

# The UI's circle pins use int(62*cos(angle)), int(62*sin(angle)).
# Recalculate rather than relying on approximate literals.
PARTS["circle_body"]["pins"] = [
    (int(62 * math.cos(math.radians(a))),
     int(62 * math.sin(math.radians(a))))
    for a in (-120, -60, 180, 0, 120, 60)
]

# Pick realistic masses here, independent of graphics sizes.
DEFAULT_MASSES = {"circle_body": 1.0, "rect_limb": .5, "leg": .5}


@dataclass
class ConvertedAlien:
    guy: Guy
    positions: list[tuple[float, float]]
    joint_anchors: list[tuple[float, float]]
    initial_angles: list[float]  # radians, in guy.get_shapes() order


def _center(part):
    dx, dy = PARTS[part["type"]]["center"]
    x, y = part["pos"]
    return (float(x) + dx, float(y) + dy)


def _pin_screen(part, pin_index):
    """Match get_world_points() in the UI (screen y points downward)."""
    pins = PARTS[part["type"]]["pins"]
    if type(pin_index) is not int or not 0 <= pin_index < len(pins):
        raise ValueError(f"Invalid pin index {pin_index} for {part['type']}")
    dx, dy = pins[pin_index]
    angle = math.radians(float(part.get("angle", 0)))
    # pygame.Vector2.rotate(-angle) in screen coordinates
    rx = dx * math.cos(angle) + dy * math.sin(angle)
    ry = -dx * math.sin(angle) + dy * math.cos(angle)
    cx, cy = _center(part)
    return (cx + rx, cy + ry)


def _bottom_offset(part):
    """Distance below the part center, accounting for a rotated rectangle."""
    kind = part["type"]
    if kind == "circle_body":
        return PARTS[kind]["size"][0] / 2
    w, h = PARTS[kind]["size"]
    a = math.radians(float(part.get("angle", 0)))
    return abs(w * math.sin(a)) / 2 + abs(h * math.cos(a)) / 2


def convert_ui_parts(placed_parts, masses=None, ground_clearance=8.0):
    """Return Guy + positions, joint anchors and initial body angles.

    `placed_parts` is the UI's list of dictionaries. No Pygame needed here.
    Requires one circle_body (the head) and every other part attached to it.
    """
    parts = list(placed_parts)
    if not parts:
        raise ValueError("The character creator has no placed parts.")
    kinds = [p.get("type") for p in parts]
    if any(kind not in PARTS for kind in kinds):
        raise ValueError("Unsupported UI part type; expected circle_body, rect_limb or leg.")
    heads = [i for i, kind in enumerate(kinds) if kind == "circle_body"]
    if len(heads) != 1:
        raise ValueError("Exactly one circle_body is required; it becomes the Head.")
    head_idx = heads[0]
    if parts[head_idx].get("parent") is not None:
        raise ValueError("The circle_body must be the root, without a parent.")
    if not math.isfinite(ground_clearance) or ground_clearance < 0:
        raise ValueError("ground_clearance must be finite and nonnegative.")

    masses = {**DEFAULT_MASSES, **(masses or {})}
    for kind in set(kinds):
        if not math.isfinite(masses[kind]) or masses[kind] <= 0:
            raise ValueError(f"Invalid mass for {kind}.")

    # Validate parent references and catch detached components or cycles.
    for i, part in enumerate(parts):
        if i == head_idx:
            continue
        visited = {i}
        curr = i
        while curr != head_idx:
            parent = parts[curr].get("parent")
            if type(parent) is not int or not (0 <= parent < len(parts)):
                raise ValueError(f"Part {i} is not connected to the head.")
            if parent in visited:
                raise ValueError(f"Attachment cycle involving part {i}.")
            visited.add(parent)
            curr = parent

    objects = {}
    for i, part in enumerate(parts):
        kind = part["type"]
        mass = float(masses[kind])
        if kind == "circle_body":
            objects[i] = Circle(mass=mass, radius=80.0)
        else:
            width, height = PARTS[kind]["size"]
            objects[i] = Rectangle(mass=mass, length=width, width=height)

    guy = Guy(objects[head_idx])
    # Shape order is head first, then UI placement order (except head).
    ordered_indices = [head_idx] + [i for i in range(len(parts)) if i != head_idx]
    for i in ordered_indices[1:]:
        guy.add_shape(objects[i])

    # Move the lowest rotated part to ground level + clearance.
    centers = {i: _center(part) for i, part in enumerate(parts)}
    highest_screen_bottom = max(
        centers[i][1] + _bottom_offset(part)
        for i, part in enumerate(parts)
    )
    head_x = centers[head_idx][0]

    def to_world(point):
        sx, sy = point
        return (float(sx) - head_x,
                highest_screen_bottom - float(sy) + float(ground_clearance))

    positions = [to_world(centers[i]) for i in ordered_indices]
    angles = [math.radians(float(parts[i].get("angle", 0))) for i in ordered_indices]
    anchors = []

    for i in ordered_indices[1:]:
        child = parts[i]
        parent_idx = child["parent"]
        parent = parts[parent_idx]
        parent_pin = _pin_screen(parent, child.get("parent_joint"))
        child_pin = _pin_screen(child, child.get("my_joint"))
        if math.dist(parent_pin, child_pin) > 3.0:
            raise ValueError(
                f"Part {i}'s joint pins are not aligned. "
                "Call update_attached_children_positions(placed_parts) "
                "in the UI before converting."
            )

        # RotaryLimitJoint measures child angle minus parent angle.
        initial_relative = (
            float(child.get("angle", 0)) - float(parent.get("angle", 0)) + 180
        ) % 360 - 180
        travel = 45 if parent["type"] == "circle_body" else 90
        joint = Joint(
            objects[parent_idx], objects[i],
            maxAngle=initial_relative + travel,
            minAngle=initial_relative - travel,
        )
        guy.add_joint(joint)
        anchors.append(to_world(parent_pin))

    return ConvertedAlien(
        guy=guy,
        positions=positions,
        joint_anchors=anchors,
        initial_angles=angles,
    )


# def create_simulation(placed_parts, masses=None, ground_clearance=8.0, **settings):
#     """Build a Simulation preserving the creator's positions, angles and pins.

#     Initial angles are radians and follow guy.get_shapes() order.
#     Calling simulation.reset() restores the creator's pose as well.
#     """
#     data = convert_ui_parts(placed_parts, masses, ground_clearance)
#     if "initial_angles" in settings or "joint_anchors" in settings:
#         raise ValueError("Initial angles and joint anchors come from the creator")
#     return Simulation(
#         data,
#         **settings,
#     )
