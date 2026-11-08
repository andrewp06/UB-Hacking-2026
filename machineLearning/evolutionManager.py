import neat
from character.simulation import Simulation
class EvolutionManager:
    def __init__(self, config):
        self.config = config
        self.population = neat.Population(config)

        self.generation = 0
        self.best_genome = None
        self.best_fitness = float("-inf")

    def evaluate_generation(self, fitness_function):
        genomes = list(self.population.population.items())

        for _, genome in genomes:
            genome.fitness = fitness_function(genome)

            if genome.fitness > self.best_fitness:
                self.best_fitness = genome.fitness
                self.best_genome = genome

        self.generation += 1

    def mock_evaluation(genomes, config):
        for _, genome in genomes:
            genome.fitness = 0.0


def evaluate_genomes(
        genomes,
        config,
        convertedAlien,
        simulation_steps,
        dt):
    
    for _, genome in genomes:

        network = neat.nn.FeedForwardNetwork.create(
            genome, config
        )

        simulation = Simulation(convertedAlien)

        #simulate
        for _ in range(simulation_steps):

            inputs = simulation.get_neural_inputs() #there needs to be something like this defined for the physics to get the infor for each joint

            outputs = network.activate(inputs)

            for joint, output in zip(convertedAlien.guy.get_joints(), outputs):
                joint.set_joint_torque(joint, output)

            simulation.step(dt)
        result = simulation.get_result()
        if(result.fell):
            result / 1.1
        genome.fitness = result.distance

