import math
import os
import pygame


# Define local connection points relative to part center (0,0)
BODY_LOCAL_POINTS = []

TRIANGLE_LOCAL_POINTS = [
    pygame.math.Vector2(0, -38),   # Top vertex joint
    pygame.math.Vector2(52, 52),   # Bottom-right vertex joint
    pygame.math.Vector2(-52, 52),  # Bottom-left vertex joint
]

LIMB_LOCAL_POINTS = [
    pygame.math.Vector2(0, -50),  # Top joint (Index 0)
    pygame.math.Vector2(0, 50),  # Bottom joint (Index 1)
]

LONG_LIMB_LOCAL_POINTS = [
    pygame.math.Vector2(0, -100),  # Top joint (Index 0)
    pygame.math.Vector2(0, 100),  # Bottom joint (Index 1)
]

LEG_LOCAL_POINTS = [
    pygame.math.Vector2(0, -50),  # Top joint (Index 0)
    pygame.math.Vector2(0, 50),  # Bottom joint (Index 1)
]


def get_part_center_offset(ptype):
  if ptype == "circle_body" or ptype == "triangle_body":
    return pygame.math.Vector2(80, 80)
  elif ptype == "rect_limb":
    return pygame.math.Vector2(25, 60)
  elif ptype == "long_rect_limb":
    return pygame.math.Vector2(25, 120)
  elif ptype == "leg":
    return pygame.math.Vector2(60, 60)
  return pygame.math.Vector2(0, 0)


def get_local_points_list(ptype):
  if ptype == "circle_body":
    return BODY_LOCAL_POINTS
  elif ptype == "triangle_body":
    return TRIANGLE_LOCAL_POINTS
  elif ptype == "rect_limb":
    return LIMB_LOCAL_POINTS
  elif ptype == "long_rect_limb":
    return LONG_LIMB_LOCAL_POINTS
  elif ptype == "leg":
    return LEG_LOCAL_POINTS
  return []


def get_world_points(part):
  ptype = part["type"]
  pos = pygame.math.Vector2(part["pos"])
  angle = part["angle"]

  cx, cy = get_part_center_offset(ptype)
  center_world = pos + pygame.math.Vector2(cx, cy)

  local_offsets = get_local_points_list(ptype)
  world_pts = []

  for offset in local_offsets:
    rotated_offset = offset.rotate(-angle)
    world_pts.append(center_world + rotated_offset)

  return world_pts


def get_straight_out_angle(parent_part, parent_joint_idx, child_part, my_joint_idx):
  """Calculates the datum angle where the child limb points straight outward from the parent part."""
  parent_pts = get_world_points(parent_part)
  joint_world_pos = parent_pts[parent_joint_idx]

  if parent_part["type"] in ["circle_body", "triangle_body"]:
    body_center = pygame.math.Vector2(parent_part["pos"]) + get_part_center_offset(
        parent_part["type"]
    )
    radial_dir = joint_world_pos - body_center
  else:
    local_pts = get_local_points_list(parent_part["type"])
    local_offset = local_pts[parent_joint_idx]
    radial_dir = local_offset.rotate(-parent_part["angle"])

  if radial_dir.length_squared() == 0:
    radial_dir = pygame.math.Vector2(0, 1)
  else:
    radial_dir = radial_dir.normalize()

  if my_joint_idx == 0:
    base_dir = pygame.math.Vector2(0, 1)
  else:
    base_dir = pygame.math.Vector2(0, -1)

  straight_angle = math.degrees(
      math.atan2(-radial_dir.y, radial_dir.x)
      - math.atan2(-base_dir.y, base_dir.x)
  )
  return straight_angle % 360


def clamp_angle_to_range(angle, center_angle, max_range=45):
  """Clamps an angle within a specified range (+/- max_range) of a center datum angle."""
  diff = (angle - center_angle + 180) % 360 - 180
  diff = max(-max_range, min(max_range, diff))
  return (center_angle + diff) % 360


def get_sub_tree(root_idx, parts):
  tree = [root_idx]
  for i, p in enumerate(parts):
    if p.get("parent") == root_idx and i not in tree:
      tree.extend(get_sub_tree(i, parts))
  return tree


def update_attached_children_positions(parts):
  """Continuously updates every child limb's position each frame to match its parent's joint pin."""
  for part in parts:
    if part["parent"] is not None:
      parent_part = parts[part["parent"]]
      parent_pts = get_world_points(parent_part)
      target_pin = parent_pts[part["parent_joint"]]

      child_pts = get_world_points(part)
      current_joint = child_pts[part["my_joint"]]

      dx = target_pin.x - current_joint.x
      dy = target_pin.y - current_joint.y
      part["pos"][0] += dx
      part["pos"][1] += dy


def render_wrapped_text(surface, text, font, color, x, y, max_width, line_spacing=2):
  """Utility to render multi-line text with word wrapping."""
  words = text.split(" ")
  lines = []
  current_line = ""

  for word in words:
    test_line = current_line + (" " if current_line else "") + word
    if font.size(test_line)[0] <= max_width:
      current_line = test_line
    else:
      if current_line:
        lines.append(current_line)
      current_line = word
  if current_line:
    lines.append(current_line)

  current_y = y
  for line in lines:
    rendered_surf = font.render(line, True, color)
    surface.blit(rendered_surf, (x, current_y))
    current_y += font.get_linesize() + line_spacing

  return current_y


def start_character_creater():

  pygame.init()

  # Window setup
  WIDTH, HEIGHT = 900, 700
  screen = pygame.display.set_mode((WIDTH, HEIGHT))
  pygame.display.set_caption("Character Creator - Instant Snap on Spawn")
  clock = pygame.time.Clock()

  # Load assets and scale cleanly for pixel art
  script_dir = os.path.dirname(__file__)

  # UI Sidebar dimensions
  UI_WIDTH = 200

  # Load Canvas Background Image ("PlanetBackground.png")
  try:
    canvas_bg_img = pygame.image.load(
        os.path.join(script_dir, "PlanetBackground.png")
    ).convert()
    canvas_bg_img = pygame.transform.scale(canvas_bg_img, (WIDTH - UI_WIDTH, HEIGHT))
  except FileNotFoundError:
    canvas_bg_img = None

  # 1. Circle Body Asset (Replaced with circleheadwhiteoutline.png)
  try:
    body_img = pygame.image.load(
        os.path.join(script_dir, "circleheadwhiteoutline.png")
    ).convert_alpha()
    body_img = pygame.transform.scale(body_img, (160, 160))
    body_thumb = pygame.transform.scale(body_img, (40, 40))
  except FileNotFoundError:
    body_img = pygame.Surface((160, 160), pygame.SRCALPHA)
    pygame.draw.circle(body_img, (0, 162, 232), (80, 80), 80)
    body_thumb = pygame.transform.scale(body_img, (40, 40))

  # 2. Triangle Body Asset
  try:
    triangle_img = pygame.image.load(
        os.path.join(script_dir, "trianglehead.png")
    ).convert_alpha()
    triangle_img = pygame.transform.scale(triangle_img, (160, 160))
    triangle_thumb = pygame.transform.scale(triangle_img, (40, 40))
  except FileNotFoundError:
    triangle_img = pygame.Surface((160, 160), pygame.SRCALPHA)
    pygame.draw.polygon(
        triangle_img, (200, 160, 220), [(80, 15), (145, 145), (15, 145)]
    )
    triangle_thumb = pygame.transform.scale(triangle_img, (40, 40))

  # 3. Rect Limb Asset
  try:
    rect_img = pygame.image.load(
        os.path.join(script_dir, "test_rect_limb.png")
    ).convert_alpha()
    rect_img = pygame.transform.scale(rect_img, (50, 120))
    rect_thumb = pygame.transform.scale(rect_img, (20, 50))
  except FileNotFoundError:
    rect_img = pygame.Surface((50, 120), pygame.SRCALPHA)
    pygame.draw.rect(rect_img, (34, 177, 76), (0, 0, 50, 120), border_radius=6)
    rect_thumb = pygame.transform.scale(rect_img, (20, 50))

  # 4. Long Rect Limb Asset
  try:
    long_img = pygame.image.load(
        os.path.join(script_dir, "test_long_rect_limb.png")
    ).convert_alpha()
    long_img = pygame.transform.scale(long_img, (50, 240))
    long_thumb = pygame.transform.scale(long_img, (18, 55))
  except FileNotFoundError:
    long_img = pygame.Surface((50, 240), pygame.SRCALPHA)
    pygame.draw.rect(long_img, (255, 140, 0), (0, 0, 50, 240), border_radius=6)
    long_thumb = pygame.transform.scale(long_img, (18, 55))

  # 5. Leg Asset
  try:
    leg_img = pygame.image.load(
        os.path.join(script_dir, "test_leg.png")
    ).convert_alpha()
    leg_img = pygame.transform.scale(leg_img, (120, 120))
  except FileNotFoundError:
    leg_img = pygame.Surface((120, 120), pygame.SRCALPHA)
    leg_img.fill((200, 100, 100))

  def get_part_image(ptype):
    if ptype == "circle_body":
      return body_img
    elif ptype == "triangle_body":
      return triangle_img
    elif ptype == "rect_limb":
      return rect_img
    elif ptype == "long_rect_limb":
      return long_img
    elif ptype == "leg":
      return leg_img
    return None

  # Organized Sidebar Items
  sidebar_items = [
      # Heads Section
      {"type": "circle_body", "rect": pygame.Rect(15, 295, 170, 40), "section": "Heads"},
      {"type": "triangle_body", "rect": pygame.Rect(15, 340, 170, 40), "section": "Heads"},
      # Limbs Section
      {"type": "rect_limb", "rect": pygame.Rect(15, 430, 170, 40), "section": "Limbs"},
      {"type": "long_rect_limb", "rect": pygame.Rect(15, 475, 170, 40), "section": "Limbs"},
  ]

  tutorial_steps = [
      "1. Click and drag parts into the window",
      "2. Attach limbs to the head and other limbs at the connecting points",
      "3. Shift click a limb that is attached to detach",
      "4. Drag parts back into this bar to delete them",
      "5. Only have one head",
      "6. Shift Click to move detached limb chains",
      "7. You cannot start if there are detached limbs",
  ]

  start_button_rect = pygame.Rect(WIDTH - 130, HEIGHT - 70, 110, 50)
  checkbox_rect = pygame.Rect(12, 535, 18, 18)
  show_points_checked = True

  placed_parts = []
  destruction_effects = []

  dragging_type = None
  dragging_index = None
  drag_mode = None
  drag_offset = [0, 0]
  current_angle = 0
  rotation_angle_offset = 0

  # Error messaging variables
  error_message = ""
  error_timer = 0

  body_angles = [-120, -60, 180, 0, 120, 60]
  for angle_deg in body_angles:
    rad = math.radians(angle_deg)
    bx = int(62 * math.cos(rad))
    by = int(62 * math.sin(rad))
    BODY_LOCAL_POINTS.append(pygame.math.Vector2(bx, by))

  running = True
  while running:
    mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos())
    keys = pygame.key.get_pressed()
    shift_held = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

    # Decrement error timer if active
    if error_timer > 0:
      error_timer -= 1

    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        running = False

      elif event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1:  # Left click
          # Check Checkbox click
          if checkbox_rect.collidepoint(mouse_pos):
            show_points_checked = not show_points_checked

          # Check "Start" button click
          elif start_button_rect.collidepoint(mouse_pos):
            bodies = [
                i
                for i, p in enumerate(placed_parts)
                if p["type"] in ["circle_body", "triangle_body"]
            ]
            can_start = False
            if len(bodies) == 1:
              connected_indices = get_sub_tree(bodies[0], placed_parts)
              if len(connected_indices) == len(placed_parts):
                can_start = True

            if can_start:
              print("Validation Successful! Returning placed_parts and straight_angles:")
              straight_angles = []
              for i, p in enumerate(placed_parts):
                if p["parent"] is not None:
                  parent_part = placed_parts[p["parent"]]
                  s_angle = get_straight_out_angle(
                      parent_part, p["parent_joint"], p, p["my_joint"]
                  )
                  straight_angles.append(s_angle)
                else:
                  straight_angles.append(0)

              return placed_parts, straight_angles
            else:
              error_message = "*Rules Not Followed*"
              error_timer = 300  # 5 seconds at 60 FPS

          elif mouse_pos.x < UI_WIDTH:
            for item in sidebar_items:
              if item["rect"].collidepoint(mouse_pos):
                # Check if trying to add a second head
                if item["type"] in ["circle_body", "triangle_body"]:
                  existing_bodies = [
                      p for p in placed_parts if p["type"] in ["circle_body", "triangle_body"]
                  ]
                  if len(existing_bodies) >= 1:
                    error_message = "*Two Heads Cannot Be Added*"
                    error_timer = 300
                    break

                dragging_type = item["type"]
                current_angle = 0
                c_off = get_part_center_offset(dragging_type)
                drag_offset = [-c_off.x, -c_off.y]
          else:
            for i in range(len(placed_parts) - 1, -1, -1):
              part = placed_parts[i]
              ptype = part["type"]
              px, py = part["pos"]
              w, h = (
                  (160, 160)
                  if ptype in ["circle_body", "triangle_body"]
                  else (50, 120)
                  if ptype == "rect_limb"
                  else (50, 240)
                  if ptype == "long_rect_limb"
                  else (120, 120)
              )
              part_rect = pygame.Rect(px, py, w, h)

              if part_rect.collidepoint(mouse_pos):
                dragging_index = i

                if part["parent"] is not None and not shift_held:
                  drag_mode = "rotate_attached"
                  parent_part = placed_parts[part["parent"]]
                  parent_pts = get_world_points(parent_part)
                  pin_world = parent_pts[part["parent_joint"]]

                  local_pts = get_local_points_list(part["type"])
                  free_joint_idx = 1 if part["my_joint"] == 0 else 0
                  unrotated_free_offset = local_pts[free_joint_idx]

                  current_mouse_angle = math.degrees(
                      math.atan2(pin_world.y - mouse_pos.y, mouse_pos.x - pin_world.x)
                  )
                  base_free_angle = math.degrees(
                      math.atan2(
                          -unrotated_free_offset.y, unrotated_free_offset.x
                      )
                  )
                  rotation_angle_offset = (
                      part["angle"] - current_mouse_angle - base_free_angle
                  )
                else:
                  drag_mode = "move"
                  target_idx = i

                  if part["parent"] is not None and shift_held:
                    part["parent"] = None
                    part["parent_joint"] = None
                    part["my_joint"] = None
                    target_idx = i

                  r_px, r_py = placed_parts[target_idx]["pos"]
                  drag_offset = [r_px - mouse_pos.x, r_py - mouse_pos.y]
                  dragging_index = target_idx
                break

      elif event.type == pygame.MOUSEBUTTONUP:
        if event.button == 1:
          if dragging_type:
            if mouse_pos.x >= UI_WIDTH:
              drop_x = mouse_pos.x + drag_offset[0]
              drop_y = mouse_pos.y + drag_offset[1]
              new_part = {
                  "type": dragging_type,
                  "pos": [drop_x, drop_y],
                  "angle": current_angle,
                  "parent": None,
                  "parent_joint": None,
                  "my_joint": None,
              }

              # Instantly check for snap if it's a limb dropped onto the canvas
              if dragging_type in ["rect_limb", "long_rect_limb", "leg"]:
                part_pts = get_world_points(new_part)
                snapped = False
                for my_j_idx, lp_world in enumerate(part_pts):
                  for target_idx, target_part in enumerate(placed_parts):
                    if target_part["type"] in [
                        "circle_body",
                        "triangle_body",
                        "rect_limb",
                        "long_rect_limb",
                        "leg",
                    ]:
                      target_pts = get_world_points(target_part)
                      for tp_idx, tp_world in enumerate(target_pts):
                        dist = lp_world.distance_to(tp_world)
                        if dist < 30:  # Snap range (30px)
                          new_part["parent"] = target_idx
                          new_part["parent_joint"] = tp_idx
                          new_part["my_joint"] = my_j_idx

                          max_range = (
                              45
                              if target_part["type"] == "circle_body"
                              else 90
                          )
                          straight_angle = get_straight_out_angle(
                              target_part, tp_idx, new_part, my_j_idx
                          )
                          new_part["angle"] = clamp_angle_to_range(
                              new_part["angle"], straight_angle, max_range
                          )

                          snapped = True
                          break
                      if snapped:
                        break
                  if snapped:
                    break

              placed_parts.append(new_part)
            dragging_type = None

          elif dragging_index is not None:
            moved_part = placed_parts[dragging_index]

            if mouse_pos.x < UI_WIDTH:
              tree_indices = get_sub_tree(dragging_index, placed_parts)
              tree_indices.sort(reverse=True)

              for idx in tree_indices:
                p_to_destroy = placed_parts.pop(idx)
                ptype = p_to_destroy["type"]
                c_off = get_part_center_offset(ptype)
                center_world = (
                    pygame.math.Vector2(p_to_destroy["pos"]) + c_off
                )
                destruction_effects.append({
                    "type": ptype,
                    "pos": center_world,
                    "angle": p_to_destroy["angle"],
                    "timer": 20,
                })

              for p in placed_parts:
                if p["parent"] in tree_indices:
                  p["parent"] = None
                  p["parent_joint"] = None
                  p["my_joint"] = None
            else:
              if moved_part["type"] in ["rect_limb", "long_rect_limb", "leg"]:
                if moved_part["parent"] is None:
                  part_pts = get_world_points(moved_part)
                  snapped = False
                  for my_j_idx, lp_world in enumerate(part_pts):
                    for target_idx, target_part in enumerate(placed_parts):
                      if target_idx == dragging_index:
                        continue
                      if target_part["type"] in [
                          "circle_body",
                          "triangle_body",
                          "rect_limb",
                          "long_rect_limb",
                          "leg",
                      ]:
                        target_pts = get_world_points(target_part)
                        for tp_idx, tp_world in enumerate(target_pts):
                          dist = lp_world.distance_to(tp_world)
                          if dist < 30:
                            moved_part["parent"] = target_idx
                            moved_part["parent_joint"] = tp_idx
                            moved_part["my_joint"] = my_j_idx

                            max_range = (
                                45
                                if target_part["type"] == "circle_body"
                                else 90
                            )
                            straight_angle = get_straight_out_angle(
                                target_part, tp_idx, moved_part, my_j_idx
                            )
                            moved_part["angle"] = clamp_angle_to_range(
                                moved_part["angle"], straight_angle, max_range
                            )

                            snapped = True
                            break
                        if snapped:
                          break
                    if snapped:
                      break

            dragging_index = None
            drag_mode = None

      elif event.type == pygame.MOUSEWHEEL:
        if dragging_type:
          if dragging_type not in ["circle_body", "triangle_body"]:
            current_angle = (current_angle + event.y * 15) % 360
        elif dragging_index is not None and drag_mode == "move":
          part = placed_parts[dragging_index]
          if part["type"] not in ["circle_body", "triangle_body"]:
            old_angle = part["angle"]
            new_angle = (old_angle + event.y * 15) % 360

            if part["parent"] is not None:
              parent_part = placed_parts[part["parent"]]
              max_range = (
                  45
                  if parent_part["type"] == "circle_body"
                  else 90
              )
              straight_angle = get_straight_out_angle(
                  parent_part, part["parent_joint"], part, part["my_joint"]
              )
              new_angle = clamp_angle_to_range(
                  new_angle, straight_angle, max_range
              )

            part["angle"] = new_angle

    # Mouse motion handling
    if dragging_index is not None:
      part = placed_parts[dragging_index]
      if drag_mode == "rotate_attached":
        parent_part = placed_parts[part["parent"]]
        parent_pts = get_world_points(parent_part)
        pin_world = parent_pts[part["parent_joint"]]

        current_mouse_angle = math.degrees(
            math.atan2(pin_world.y - mouse_pos.y, mouse_pos.x - pin_world.x)
        )
        local_pts = get_local_points_list(part["type"])
        free_joint_idx = 1 if part["my_joint"] == 0 else 0
        unrotated_free_offset = local_pts[free_joint_idx]

        raw_angle = (
            current_mouse_angle + base_free_angle + rotation_angle_offset
        ) % 360

        max_range = (
            45
            if parent_part["type"] == "circle_body"
            else 90
        )
        straight_angle = get_straight_out_angle(
            parent_part,
            parent_joint_idx=part["parent_joint"],
            child_part=part,
            my_joint_idx=part["my_joint"],
        )
        part["angle"] = clamp_angle_to_range(raw_angle, straight_angle, max_range)

      elif drag_mode == "move":
        old_x, old_y = part["pos"]
        new_x = mouse_pos.x + drag_offset[0]
        new_y = mouse_pos.y + drag_offset[1]
        dx = new_x - old_x
        dy = new_y - old_y

        tree = get_sub_tree(dragging_index, placed_parts)
        for idx in tree:
          placed_parts[idx]["pos"][0] += dx
          placed_parts[idx]["pos"][1] += dy

    update_attached_children_positions(placed_parts)

    # --- DRAWING / RENDERING ---
    screen.fill((240, 240, 240))

    # 1. DRAW CANVAS BACKGROUND (PlanetBackground.png behind building area)
    if canvas_bg_img:
      screen.blit(canvas_bg_img, (UI_WIDTH, 0))
    else:
      pygame.draw.rect(screen, (240, 240, 240), (UI_WIDTH, 0, WIDTH - UI_WIDTH, HEIGHT))

    # 2. DRAW UI SIDEBAR BACKGROUND & ORGANIZED SECTIONS
    pygame.draw.rect(screen, (50, 50, 50), (0, 0, UI_WIDTH, HEIGHT))
    pygame.draw.line(screen, (200, 200, 200), (UI_WIDTH, 0), (UI_WIDTH, HEIGHT), 3)

    font = pygame.font.SysFont(None, 18)
    tut_font = pygame.font.SysFont(None, 15)
    section_font = pygame.font.SysFont(None, 22, bold=True)

    # Render "Tutorial" Header & Wrapped Instructions
    tut_label = section_font.render("Tutorial", True, (255, 215, 0))
    screen.blit(tut_label, (15, 10))

    y_offset = 32
    for step in tutorial_steps:
      y_offset = render_wrapped_text(
          screen, step, tut_font, (220, 220, 220), 15, y_offset, UI_WIDTH - 30, line_spacing=2
      )
      y_offset += 2

    # Render "Heads" & "Limbs" Headers
    heads_label = section_font.render("Heads", True, (200, 200, 200))
    limbs_label = section_font.render("Limbs", True, (200, 200, 200))
    screen.blit(heads_label, (15, 270))
    screen.blit(limbs_label, (15, 405))

    for item in sidebar_items:
      pygame.draw.rect(screen, (80, 80, 80), item["rect"], border_radius=6)
      pygame.draw.rect(screen, (120, 120, 120), item["rect"], 2, border_radius=6)

      if item["type"] == "circle_body":
        text = font.render("Circle Head", True, (255, 255, 255))
        screen.blit(body_thumb, (item["rect"].x + 6, item["rect"].centery - 20))
        screen.blit(text, (item["rect"].x + 50, item["rect"].centery - 8))
      elif item["type"] == "triangle_body":
        text = font.render("Triangle Head", True, (255, 255, 255))
        screen.blit(triangle_thumb, (item["rect"].x + 6, item["rect"].centery - 20))
        screen.blit(text, (item["rect"].x + 50, item["rect"].centery - 8))
      elif item["type"] == "rect_limb":
        text = font.render("Rect Limb", True, (255, 255, 255))
        screen.blit(rect_thumb, (item["rect"].x + 10, item["rect"].centery - 22))
        screen.blit(text, (item["rect"].x + 50, item["rect"].centery - 8))
      elif item["type"] == "long_rect_limb":
        text = font.render("Long Limb", True, (255, 255, 255))
        screen.blit(long_thumb, (item["rect"].x + 12, item["rect"].centery - 22))
        screen.blit(text, (item["rect"].x + 50, item["rect"].centery - 8))

    # Checkbox Rendering
    pygame.draw.rect(screen, (255, 255, 255), checkbox_rect, border_radius=4)
    pygame.draw.rect(screen, (120, 120, 120), checkbox_rect, 2, border_radius=4)
    if show_points_checked:
      pygame.draw.line(
          screen,
          (0, 150, 0),
          (checkbox_rect.x + 3, checkbox_rect.centery),
          (checkbox_rect.centerx - 1, checkbox_rect.bottom - 4),
          2,
      )
      pygame.draw.line(
          screen,
          (0, 150, 0),
          (checkbox_rect.centerx - 1, checkbox_rect.bottom - 4),
          (checkbox_rect.right - 3, checkbox_rect.top + 3),
          2,
      )
    cb_label = font.render("Show Connecting Points", True, (220, 220, 220))
    screen.blit(cb_label, (checkbox_rect.right + 6, checkbox_rect.centery - 8))

    # Determine Start Button State & Color
    bodies = [
        i for i, p in enumerate(placed_parts) if p["type"] in ["circle_body", "triangle_body"]
    ]
    can_start = False
    if len(bodies) == 1:
      connected_indices = get_sub_tree(bodies[0], placed_parts)
      if len(connected_indices) == len(placed_parts):
        can_start = True

    if can_start:
      btn_color = (
          (70, 180, 70)
          if start_button_rect.collidepoint(mouse_pos)
          else (50, 150, 50)
      )
      btn_text_color = (255, 255, 255)
      border_col = (30, 100, 30)
    else:
      btn_color = (130, 130, 130)  # Greyed out
      btn_text_color = (200, 200, 200)
      border_col = (90, 90, 90)

    # Draw "Start" Button in Bottom Right
    pygame.draw.rect(screen, btn_color, start_button_rect, border_radius=8)
    pygame.draw.rect(screen, border_col, start_button_rect, 2, border_radius=8)
    btn_font = pygame.font.SysFont(None, 24, bold=True)
    btn_text = btn_font.render("Start", True, btn_text_color)
    screen.blit(
        btn_text,
        (
            start_button_rect.centerx - btn_text.get_width() // 2,
            start_button_rect.centery - btn_text.get_height() // 2,
        ),
    )

    # Draw Fading Error Message in Bottom Left of UI Bar if Active
    if error_timer > 0:
      err_font = pygame.font.SysFont(None, 15, bold=True)
      alpha = int(255 * (error_timer / 300.0))
      err_surf = err_font.render(error_message, True, (255, 50, 50))
      err_surf.set_alpha(alpha)
      screen.blit(err_surf, (15, HEIGHT - 50))

    def is_joint_attached(part, part_idx, j_idx):
      if part_idx is None:
        return False
      if part["parent"] is not None and part["my_joint"] == j_idx:
        return True
      for idx, other in enumerate(placed_parts):
        if other["parent"] == part_idx and other["parent_joint"] == j_idx:
          return True
      return False

    def draw_part_surface(part, part_idx):
      ptype = part["type"]
      angle = part["angle"]
      c_off = get_part_center_offset(ptype)
      cx, cy = int(c_off.x), int(c_off.y)
      local_offsets = get_local_points_list(ptype)
      base_img = get_part_image(ptype)

      surf = pygame.Surface(base_img.get_size(), pygame.SRCALPHA)
      surf.blit(base_img, (0, 0))

      if show_points_checked:
        for j_idx, offset in enumerate(local_offsets):
          dot_pos = pygame.math.Vector2(cx, cy) + offset
          color = (
              (144, 238, 144)
              if is_joint_attached(part, part_idx, j_idx)
              else (0, 0, 0)
          )
          pygame.draw.circle(surf, color, (int(dot_pos.x), int(dot_pos.y)), 10)

      return pygame.transform.rotate(surf, angle)

    def draw_part(surface, part, part_idx=None):
      ptype = part["type"]
      x, y = part["pos"]
      angle = part["angle"]

      rot_img = draw_part_surface(part, part_idx)
      c_off = get_part_center_offset(ptype)
      rot_rect = rot_img.get_rect(center=(x + c_off.x, y + c_off.y))
      surface.blit(rot_img, rot_rect.topleft)

    # 3. DRAW PLACED PARTS (Split into Limbs first, then Bodies on top)
    limb_parts = [
        (idx, p) for idx, p in enumerate(placed_parts) if p["type"] not in ["circle_body", "triangle_body"]
    ]
    body_parts = [
        (idx, p) for idx, p in enumerate(placed_parts) if p["type"] in ["circle_body", "triangle_body"]
    ]

    for idx, part in limb_parts:
      draw_part(screen, part, idx)
    for idx, part in body_parts:
      draw_part(screen, part, idx)

    # 4. DRAW DESTRUCTION / POP ANIMATIONS & FADE OUTS
    for fx in destruction_effects[:]:
      progress = 1.0 - (fx["timer"] / 20.0)
      alpha = int(255 * (1.0 - progress))

      base_img = get_part_image(fx["type"])
      fade_surf = pygame.Surface(base_img.get_size(), pygame.SRCALPHA)
      fade_surf.blit(base_img, (0, 0))
      fade_surf.set_alpha(max(0, alpha))
      rot_img = pygame.transform.rotate(fade_surf, fx["angle"])

      c_off = get_part_center_offset(fx["type"])
      rot_rect = rot_img.get_rect(center=(fx["pos"].x, fx["pos"].y))
      screen.blit(rot_img, rot_rect.topleft)

      for i in range(6):
        angle_rad = math.radians(i * 60 + progress * 30)
        line_len = 15 + progress * 40
        end_x = fx["pos"].x + math.cos(angle_rad) * line_len
        end_y = fx["pos"].y + math.sin(angle_rad) * line_len
        pygame.draw.line(
            screen, (255, 50, 50), (fx["pos"].x, fx["pos"].y), (end_x, end_y), 3
        )

      fx["timer"] -= 1
      if fx["timer"] <= 0:
        destruction_effects.remove(fx)

    # 5. DRAW PREVIEW OF NEW ITEM BEING DRAGGED FROM SIDEBAR
    if dragging_type:
      preview_part = {
          "type": dragging_type,
          "pos": [
              mouse_pos.x + drag_offset[0],
              mouse_pos.y + drag_offset[1],
          ],
          "angle": current_angle,
      }
      draw_part(screen, preview_part, None)

    pygame.display.flip()
    clock.tick(60)

  pygame.quit()


if __name__ == "__main__":
  start_character_creater()