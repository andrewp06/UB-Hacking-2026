import pygame

pygame.init()

screen = pygame.display.set_mode((640, 640))


leg_img = pygame.image.load('Game/test_leg.png').convert_alpha()

leg_img = pygame.transform.scale(leg_img,
                                 (leg_img.get_width() * 5,
                                  leg_img.get_height() * 5))


running = True
x = 0
clock = pygame.time.Clock()

delta_time = 0.1

while running:
    screen.fill((255, 255 ,255))

    screen.blit(leg_img, (x,30))


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()

    delta_time = clock.tick(60) /1000
    delta_time = max(0.001, min(0.1, delta_time))

pygame.quit()