from functools import partial

import neat
from character.simulation import Simulation
import multiprocessing

class EvolutionManager:
    def __init__(self, config):
        self.config = config
        self.population = neat.Population(config)

        self.generation = 0
        self.best_genome = None
        self.best_fitness = float("-inf")

    def run(self, convertedAlien, steps, dt, generations):

        fitness_function = partial(
            evaluate_genome,
            convertedAlien=convertedAlien,
            steps=steps,
            dt=dt
        )

        workers = 4

        with neat.ParallelEvaluator(
            workers, fitness_function
        ) as evaluator:

            winner = self.population.run(
                evaluator.evaluate,
                generations
            )

        return winner
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