import neat
import configparser
import tempfile
import os
from character.joint import Joint
from character.guy import Guy
import character.circle
import character.rectangle
from .guyMorphology import GuyMorphology

def create_neat_config(morphology, base_config_path):
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(base_config_path)

    joint_count = morphology.joint_count

    input_count = 2 + (2 * joint_count)
    output_count = joint_count

    parser["DefaultGenome"]["num_inputs"] = str(input_count)
    parser["DefaultGenome"]["num_outputs"] = str(output_count)

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".ini",
        delete=False
    ) as file:
        parser.write(file)
        config_path = file.name

    try:
        config = neat.Config(
            neat.DefaultGenome,
            neat.DefaultReproduction,
            neat.DefaultSpeciesSet,
            neat.DefaultStagnation,
            config_path
        )
    finally:
        os.remove(config_path)

    return config

if __name__ == "__main__":
    head = character.circle.Circle(5)
    guy = Guy(head)
    leg = character.rectangle.Rectangle(2, 2)
    joint = Joint(head, leg, 0, 180)
    guy.add_joint(joint)
    guy.add_shape(leg)

    morphology = GuyMorphology(guy)

    create_neat_config(morphology, "machineLearning/ml_config").save("Test")