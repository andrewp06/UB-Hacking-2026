import neat

class EvolutionManager:
    def __init__(self, config):
        self.config = config
        self.population = neat.Population(config)

        self.generation = 0
        self.best_genome = None
        self.best_fitness = float("-inf")

    def evaluate_generation(self, fitness_function):
        genomes = list(self.population.population.items())

        for genome_id, genome in genomes:
            genome.fitness = fitness_function(genome)

            if genome.fitness > self.best_fitness:
                self.best_fitness = genome.fitness
                self.best_genome = genome

        self.generation += 1

    def mock_evaluation(genomes, config):
        for genome_id, genome in genomes:
            genome.fitness = 0.0


def evaluate_genomes(
        genomes,
        config,
        guy,
        physics,
        simulation_steps,
        dt):

    for _, genome in genomes:

        network = neat.nn.FeedForwardNetwork.create(
            genome, config
        )

        # Create alien
        alien = physics.create_alien(guy)
        initial_x = alien.get_position().x

        #simulate
        for _ in range(simulation_steps):

            inputs = alien.get_neural_inputs() #there needs to be something like this defined for the physics to get the infor for each joint

            outputs = network.activate(inputs)

            for joint, output in zip(alien.joints, outputs):
                joint.apply_torque(output)

            physics.step(dt)

        final_x = alien.get_position().x

        genome.fitness = final_x - initial_x

