

import pickle

from Game.char_adapter import convert_ui_parts
from Game.char_creator import start_character_creater
from machineLearning.guyMorphology import GuyMorphology
from machineLearning.dynamicConfig import create_neat_config
from machineLearning.evolutionManager import EvolutionManager

STEPS = 600
DT = 1/60
GENERATIONS = 100

def main():
    placed_parts = start_character_creater()
    converted_guy = convert_ui_parts(placed_parts)
    config = create_neat_config(GuyMorphology(converted_guy.guy), "machineLearning/ml_config")
    evo_manager = EvolutionManager(config)
    winner = evo_manager.run(converted_guy, STEPS, DT, GENERATIONS)

    with open("winner.pkl", "wb") as file:
        pickle.dump(winner, file)
    print("winner")
    while True:
        run_winner = evo_manager.run_winner(winner, converted_guy, STEPS, DT)

if __name__ == "__main__":
    main()