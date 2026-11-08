from functools import partial

import neat
from character.simulation import Simulation

class EvolutionManager:
    def __init__(self, config):
        self.config = config
        self.population = neat.Population(config)

        self.generation = 0
        self.best_genome = None
        self.best_fitness = float("-inf")

    def run(self, screen, convertedAlien, steps, dt, generations):

        import pygame

        fitness_function = partial(
            evaluate_genome,
            convertedAlien=convertedAlien,
            steps=steps,
            dt=dt
        )

        workers = 4

        # Load loading bar image
        loading_image = pygame.image.load("Game/loadingbar.png").convert()

        width, height = screen.get_size()

        # Dim overlay
        overlay = pygame.Surface((width, height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(160)

        # Loading bar dimensions
        bar_width = 250
        bar_height = 50
        bar_x = (width - bar_width) // 2
        bar_y = (height - bar_height) // 2

        for generation in range(generations):

            with neat.ParallelEvaluator(
                workers, fitness_function
            ) as evaluator:

                self.population.run(
                    evaluator.evaluate,
                    1
                )

            # Calculate progress
            progress = (generation + 1) / generations

            # Dim screen
            screen.blit(overlay, (0, 0))

            # Draw loading bar background
            pygame.draw.rect(
                screen,
                (70, 70, 70),
                (bar_x, bar_y, bar_width, bar_height)
            )

            # Calculate how much of the image to reveal
            filled_width = int(bar_width * progress)

            if filled_width > 0:
                screen.blit(
                    loading_image,
                    (bar_x, bar_y),
                    pygame.Rect(0, 0, filled_width, bar_height)
                )

            # Generation counter
            font = pygame.font.SysFont(None, 32)

            text = font.render(
                f"Generation {generation + 1} / {generations}",
                True,
                (255, 255, 255)
            )

            screen.blit(
                text,
                (bar_x, bar_y + bar_height + 15)
            )

            pygame.display.flip()

        return self.population.best_genome

        
    def run_winner(self, winner, convertedAlien, steps, dt, screen = None):
        network = neat.nn.FeedForwardNetwork.create(
            winner, self.config
        )

        while True:
            simulation = Simulation(convertedAlien)

            result = simulation.run(
                steps=steps,
                dt=dt,
                render=True,
                network=network,
                screen=screen
            )

            if result != "rerun":
                break
        return result


def evaluate_genome(genome, config, convertedAlien, steps, dt):
    network = neat.nn.FeedForwardNetwork.create(genome, config)

    simulation = Simulation(convertedAlien)

    for _ in range(steps):
        inputs = simulation.get_network_inputs()
        outputs = network.activate(inputs)

        for joint, output in zip(simulation.guy.get_joints(), outputs):
            simulation.set_joint_torque(joint, output)

        result = simulation.step(dt)

        if result.fell:
            break

    result = simulation.get_result()
    return float(result.distance)