import pygame

def main_menu(screen):

    pygame.init()

    width, height = screen.get_size()
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 40)
    title_font = pygame.font.Font(None, 80)

    buttons = {
        "New Alien": pygame.Rect(width // 2 - 150, height // 2 - 60, 300, 60),
        "Load Alien": pygame.Rect(width // 2 - 150, height // 2 + 20, 300, 60),
        "Exit": pygame.Rect(width // 2 - 150, height // 2 + 100, 300, 60),
    }

    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "Exit"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for name, rect in buttons.items():
                    if rect.collidepoint(event.pos):
                        return name

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "Exit"

        # Background
        screen.fill((23, 29, 42))

        # Title
        title = title_font.render("Alien Creator", True, (240, 240, 245))
        screen.blit(
            title,
            title.get_rect(center=(width // 2, height // 2 - 180))
        )

        # Buttons
        for name, rect in buttons.items():
            hovered = rect.collidepoint(mouse_pos)

            color = (75, 125, 180) if hovered else (50, 85, 125)

            pygame.draw.rect(screen, color, rect, border_radius=10)

            text = font.render(name, True, (255, 255, 255))
            screen.blit(text, text.get_rect(center=rect.center))

        pygame.display.flip()
        clock.tick(60)

    return "Exit"