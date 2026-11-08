import math
import os
import pygame


# Define local connection points relative to part center (0,0)
BODY_LOCAL_POINTS = []

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
  if ptype == "circle_body":
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

  if parent_part["type"] == "circle_body":
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

      # Check where child's connecting joint currently is in world coordinates
      child_pts = get_world_points(part)
      current_joint = child_pts[part["my_joint"]]

      # Shift child part so its joint snaps directly onto the parent's pin
      dx = target_pin.x - current_joint.x
      dy = target_pin.y - current_joint.y
      part["pos"][0] += dx
      part["pos"][1] += dy


def start_character_creater():

  pygame.init()

  # Window setup
  WIDTH, HEIGHT = 900, 700
  screen = pygame.display.set_mode((WIDTH, HEIGHT))
  pygame.display.set_caption("Character Creator - Start Button Validation")
  clock = pygame.time.Clock()

  # Load assets and scale cleanly for pixel art
  script_dir = os.path.dirname(__file__)

  # 1. Body Asset
  try:
    body_img = pygame.image.load(
        os.path.join(script_dir, "test_body.png")
    ).convert_alpha()
    body_img = pygame.transform.scale(body_img, (160, 160))
    body_thumb = pygame.transform.scale(body_img, (50, 50))
  except FileNotFoundError:
    body_img = pygame.Surface((160, 160), pygame.SRCALPHA)
    pygame.draw.circle(body_img, (0, 162, 232), (80, 80), 80)
    body_thumb = pygame.transform.scale(body_img, (50, 50))

  # 2. Rect Limb Asset
  try:
    rect_img = pygame.image.load(
        os.path.join(script_dir, "test_rect_limb.png")
    ).convert_alpha()
    rect_img = pygame.transform.scale(rect_img, (50, 120))
    rect_thumb = pygame.transform.scale(rect_img, (30, 50))
  except FileNotFoundError:
    rect_img = pygame.Surface((50, 120), pygame.SRCALPHA)
    pygame.draw.rect(rect_img, (34, 177, 76), (0, 0, 50, 120), border_radius=6)
    rect_thumb = pygame.transform.scale(rect_img, (30, 50))

  # 3. Long Rect Limb Asset
  try:
    long_img = pygame.image.load(
        os.path.join(script_dir, "test_long_rect_limb.png")
    ).convert_alpha()
    long_img = pygame.transform.scale(long_img, (50, 240))
    long_thumb = pygame.transform.scale(long_img, (25, 55))
  except FileNotFoundError:
    long_img = pygame.Surface((50, 240), pygame.SRCALPHA)
    pygame.draw.rect(long_img, (255, 140, 0), (0, 0, 50, 240), border_radius=6)
    long_thumb = pygame.transform.scale(long_img, (25, 55))

  # 4. Leg Asset
  try:
    leg_img = pygame.image.load(
        os.path.join(script_dir, "test_leg.png")
    ).convert_alpha()
    leg_img = pygame.transform.scale(leg_img, (120, 120))
    leg_thumb = pygame.transform.scale(leg_img, (50, 50))
  except FileNotFoundError:
    leg_img = pygame.Surface((120, 120), pygame.SRCALPHA)
    leg_img.fill((200, 100, 100))
    leg_thumb = pygame.transform.scale(leg_img, (50, 50))

  def get_part_image(ptype):
    if ptype == "circle_body":
      return body_img
    elif ptype == "rect_limb":
      return rect_img
    elif ptype == "long_rect_limb":
      return long_img
    elif ptype == "leg":
      return leg_img
    return None

  # UI Sidebar & Button dimensions
  UI_WIDTH = 200
  sidebar_items = [
      {"type": "leg", "rect": pygame.Rect(20, 30, 160, 65)},
      {"type": "circle_body", "rect": pygame.Rect(20, 105, 160, 65)},
      {"type": "rect_limb", "rect": pygame.Rect(20, 180, 160, 65)},
      {"type": "long_rect_limb", "rect": pygame.Rect(20, 255, 160, 65)},
  ]

  start_button_rect = pygame.Rect(WIDTH - 130, HEIGHT - 70, 110, 50)

  # List of placed parts and active destruction animation effects
  placed_parts = []
  destruction_effects = []

  # Interaction state variables
  dragging_type = None
  dragging_index = None
  drag_mode = None
  drag_offset = [0, 0]
  current_angle = 0
  rotation_angle_offset = 0

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

    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        running = False

      elif event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1:  # Left click
          # Check if "Start" button was clicked
          if start_button_rect.collidepoint(mouse_pos):
            # Validate character build
            bodies = [
                i
                for i, p in enumerate(placed_parts)
                if p["type"] == "circle_body"
            ]
            if len(bodies) != 1:
              print(
                  "Validation Failed: You must have exactly 1 Body (Head)."
                  f" Found: {len(bodies)}"
              )
            else:
              body_idx = bodies[0]
              connected_indices = get_sub_tree(body_idx, placed_parts)
              if len(connected_indices) == len(placed_parts):
                print("Validation Successful! Returning placed_parts:")
                for p in placed_parts:
                  print(p)
                return placed_parts
              else:
                print(
                    "Validation Failed: Some limbs are not connected to the"
                    " body or are floating!"
                )

          elif mouse_pos.x < UI_WIDTH:
            for item in sidebar_items:
              if item["rect"].collidepoint(mouse_pos):
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
                  if ptype == "circle_body"
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
                          "rect_limb",
                          "long_rect_limb",
                          "leg",
                      ]:
                        target_pts = get_world_points(target_part)
                        for tp_idx, tp_world in enumerate(target_pts):
                          dist = lp_world.distance_to(tp_world)
                          if dist < 25:
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
          if dragging_type != "circle_body":
            current_angle = (current_angle + event.y * 15) % 360
        elif dragging_index is not None and drag_mode == "move":
          part = placed_parts[dragging_index]
          if part["type"] != "circle_body":
            old_angle = part["angle"]
            new_angle = (old_angle + event.y * 15) % 360

            if part["parent"] is not None:
              parent_part = placed_parts[part["parent"]]
              max_range = 45 if parent_part["type"] == "circle_body" else 90
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

        max_range = 45 if parent_part["type"] == "circle_body" else 90
        straight_angle = get_straight_out_angle(
            parent_part, parent_joint_idx=part["parent_joint"], child_part=part, my_joint_idx=part["my_joint"]
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

    # Continuously update/sync all child limbs to their parent pins every single frame
    update_attached_children_positions(placed_parts)

    # --- DRAWING / RENDERING ---
    screen.fill((240, 240, 240))

    # 1. DRAW UI SIDEBAR BACKGROUND & BUTTONS FIRST
    pygame.draw.rect(screen, (50, 50, 50), (0, 0, UI_WIDTH, HEIGHT))
    pygame.draw.line(screen, (200, 200, 200), (UI_WIDTH, 0), (UI_WIDTH, HEIGHT), 3)

    font = pygame.font.SysFont(None, 20)
    for item in sidebar_items:
      pygame.draw.rect(screen, (80, 80, 80), item["rect"], border_radius=6)
      pygame.draw.rect(screen, (120, 120, 120), item["rect"], 2, border_radius=6)

      if item["type"] == "leg":
        text = font.render("Leg Part", True, (255, 255, 255))
        screen.blit(leg_thumb, (item["rect"].x + 5, item["rect"].centery - 25))
        screen.blit(text, (item["rect"].x + 60, item["rect"].centery - 10))
      elif item["type"] == "circle_body":
        text = font.render("Body", True, (255, 255, 255))
        screen.blit(body_thumb, (item["rect"].x + 5, item["rect"].centery - 25))
        screen.blit(text, (item["rect"].x + 60, item["rect"].centery - 10))
      elif item["type"] == "rect_limb":
        text = font.render("Rect Limb", True, (255, 255, 255))
        screen.blit(rect_thumb, (item["rect"].x + 10, item["rect"].centery - 25))
        screen.blit(text, (item["rect"].x + 50, item["rect"].centery - 10))
      elif item["type"] == "long_rect_limb":
        text = font.render("Long Limb", True, (255, 255, 255))
        screen.blit(long_thumb, (item["rect"].x + 12, item["rect"].centery - 25))
        screen.blit(text, (item["rect"].x + 50, item["rect"].centery - 10))

    # Draw "Start" Button in Bottom Right
    btn_color = (
        (70, 180, 70)
        if start_button_rect.collidepoint(mouse_pos)
        else (50, 150, 50)
    )
    pygame.draw.rect(screen, btn_color, start_button_rect, border_radius=8)
    pygame.draw.rect(screen, (30, 100, 30), start_button_rect, 2, border_radius=8)
    btn_font = pygame.font.SysFont(None, 24, bold=True)
    btn_text = btn_font.render("Start", True, (255, 255, 255))
    screen.blit(
        btn_text,
        (
            start_button_rect.centerx - btn_text.get_width() // 2,
            start_button_rect.centery - btn_text.get_height() // 2,
        ),
    )

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

    # 2. DRAW PLACED PARTS
    for idx, part in enumerate(placed_parts):
      draw_part(screen, part, idx)

    # 3. DRAW DESTRUCTION / POP ANIMATIONS & FADE OUTS
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

    # 4. DRAW PREVIEW OF NEW ITEM BEING DRAGGED FROM SIDEBAR
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