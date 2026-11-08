import pygame

def get_simulation_settings(screen, width):
    total_time = "10"
    generations = "50"

    active_field = "time"
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 32)
    title_font = pygame.font.SysFont(None, 48)

    box_width = 350
    box_height = 55
    box_x = (width - box_width) // 2

    time_box = pygame.Rect(box_x, 260, box_width, box_height)
    gen_box = pygame.Rect(box_x, 380, box_width, box_height)

    while True:
        screen.fill((35, 35, 35))

        title = title_font.render(
            "Simulation Settings", True, (255, 255, 255)
        )
        screen.blit(
            title,
            (width // 2 - title.get_width() // 2, 150)
        )

        # Labels
        time_label = font.render(
            "Total Simulation Time (seconds)", True, (220, 220, 220)
        )
        gen_label = font.render(
            "Number of Generations", True, (220, 220, 220)
        )

        screen.blit(time_label, (box_x, 225))
        screen.blit(gen_label, (box_x, 345))

        # Draw input boxes
        pygame.draw.rect(screen, (55, 55, 55), time_box, border_radius=8)
        pygame.draw.rect(screen, (55, 55, 55), gen_box, border_radius=8)

        time_color = (100, 180, 255) if active_field == "time" else (130, 130, 130)
        gen_color = (100, 180, 255) if active_field == "generations" else (130, 130, 130)

        pygame.draw.rect(screen, time_color, time_box, 3, border_radius=8)
        pygame.draw.rect(screen, gen_color, gen_box, 3, border_radius=8)

        # Input text / placeholders
        time_display = total_time if total_time else "Enter time in seconds..."
        gen_display = generations if generations else "Enter generation count..."

        time_text = font.render(
            time_display, True,
            (255, 255, 255) if total_time else (150, 150, 150)
        )
        gen_text = font.render(
            gen_display, True,
            (255, 255, 255) if generations else (150, 150, 150)
        )

        screen.blit(time_text, (time_box.x + 15, time_box.y + 13))
        screen.blit(gen_text, (gen_box.x + 15, gen_box.y + 13))

        # Instructions
        instructions = pygame.font.SysFont(None, 24).render(
            "Click a box to type | TAB to switch | ENTER to continue \n Increasing either of these values will Increase time to generate a result",
            True, (180, 180, 180)
        )
        screen.blit(
            instructions,
            (width // 2 - instructions.get_width() // 2, 480)
        )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            if event.type == pygame.MOUSEBUTTONDOWN:
                if time_box.collidepoint(event.pos):
                    active_field = "time"
                elif gen_box.collidepoint(event.pos):
                    active_field = "generations"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    active_field = (
                        "generations" if active_field == "time" else "time"
                    )

                elif event.key == pygame.K_BACKSPACE:
                    if active_field == "time":
                        total_time = total_time[:-1]
                    else:
                        generations = generations[:-1]

                elif event.key == pygame.K_RETURN:
                    try:
                        time_value = float(total_time)
                        gen_value = int(generations)

                        if time_value > 0 and gen_value > 0:
                            return time_value, gen_value
                    except ValueError:
                        pass

                elif event.unicode.isdigit() or (
                    active_field == "time" and event.unicode == "."
                    and "." not in total_time
                ):
                    if active_field == "time":
                        total_time += event.unicode
                    else:
                        generations += event.unicode

        pygame.display.flip()
        clock.tick(60)
