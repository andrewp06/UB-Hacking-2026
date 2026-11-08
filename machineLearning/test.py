# from .dynamicConfig import create_neat_config
# from .evolutionManager import EvolutionManager
# import neat

# def test_fitness(genomes, config):
#     for genome_id, genome in genomes:
#         network = neat.nn.FeedForwardNetwork.create(
#             genome, config
#         )

#         inputs = [0.5] * config.genome_config.num_inputs
#         outputs = network.activate(inputs)

#         genome.fitness = sum(abs(x) for x in outputs)

# # Use a temporary morphology with 4 joints
# class MockMorphology:
#     joint_count = 4

# for joints in [4, 6, 8]:
#     morphology = MockMorphology()
#     morphology.joint_count = joints

#     config = create_neat_config(
#         morphology,
#         "machineLearning/ml_config"
#     )

#     print(
#         joints,
#         config.genome_config.num_inputs,
#         config.genome_config.num_outputs
#     )
