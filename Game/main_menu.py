
import math
import os
import pygame


def _load_alien_sprites():
    """Load the existing alien sprites."""
    asset_dir = os.path.dirname(__file__)

    head = pygame.image.load(
        os.path.join(asset_dir, "circleheadwhiteoutline.png")
    ).convert_alpha()
    head = pygame.transform.smoothscale(head, (120, 120))

    limb = pygame.image.load(
        os.path.join(asset_dir, "shortlimb.png")
    ).convert_alpha()
    limb = pygame.transform.smoothscale(limb, (35, 84))

    return head, limb


def _draw_limb(screen, sprite, pivot, angle):
    """Rotate a limb around its attachment point."""
    radians = math.radians(angle)
    half_length = sprite.get_height() / 2

    center = (
        pivot[0] + math.sin(radians) * half_length,
        pivot[1] + math.cos(radians) * half_length
    )

    rotated = pygame.transform.rotate(sprite, angle)
    rect = rotated.get_rect(center=(
        round(center[0]), round(center[1])
    ))
    screen.blit(rotated, rect)


def _draw_alien(screen, head, limb, x, y, elapsed):
    """Draw the animated alien in the lower-right corner."""
    y += math.sin(elapsed * 2) * 4

    # Legs
    _draw_limb(screen, limb, (x - 25, y + 43), -12)
    _draw_limb(screen, limb, (x + 25, y + 43), 12)

    # Right arm
    _draw_limb(screen, limb, (x - 51, y - 18), -28)

    # Left arm waving
    wave = 135 + 18 * math.sin(elapsed * 5)
    _draw_limb(screen, limb, (x + 51, y - 18), wave)

    # Circular body
    screen.blit(
        head,
        head.get_rect(center=(round(x), round(y)))
    )


def main_menu(screen):
    pygame.init()

    width, height = screen.get_size()
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 40)

    # Load the new background, falling back to the existing one.
    asset_dir = os.path.dirname(__file__)
    background_path = os.path.join(asset_dir, "titlescreen.png")

    if not os.path.isfile(background_path):
        background_path = os.path.join(
            asset_dir, "titlescreenbg.png"
        )

    background = pygame.image.load(background_path).convert()
    background = pygame.transform.smoothscale(
        background, (width, height)
    )

    head, limb = _load_alien_sprites()

    # Preserve original button positions.
    buttons = {
        "New Alien": pygame.Rect(
            width // 2 - 150, height // 2, 300, 60
        ),
        "Exit": pygame.Rect(
            width // 2 - 150, height // 2 + 75, 300, 60
        ),
    }

    elapsed = 0.0
    running = True

    while running:
        elapsed += clock.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "Exit"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for name, rect in buttons.items():
                    if rect.collidepoint(event.pos):
                        return name

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "Exit"

        # Background without additional title text.
        screen.blit(background, (0, 0))

        # Original buttons and hover behavior.
        for name, rect in buttons.items():
            hovered = rect.collidepoint(mouse_pos)

            color = (
                (205, 185, 235)
                if hovered
                else (180, 155, 215)
            )

            pygame.draw.rect(
                screen, color, rect, border_radius=10
            )

            text = font.render(
                name, True, (255, 255, 255)
            )
            screen.blit(
                text, text.get_rect(center=rect.center)
            )

        # Animated alien in lower-right corner.
        _draw_alien(
            screen, head, limb,
            width - 130, height - 170,
            elapsed
        )

        pygame.display.flip()

    return "Exit"
