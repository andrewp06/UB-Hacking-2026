
import pygame
import pickle

from Game.main_menu import main_menu
from Game.char_adapter import convert_ui_parts
from Game.char_creator import start_character_creater, HEIGHT, WIDTH
from machineLearning.guyMorphology import GuyMorphology
from machineLearning.dynamicConfig import create_neat_config
from machineLearning.evolutionManager import EvolutionManager

STEPS = 600
DT = 1/60
GENERATIONS = 100

def main():
    pygame.init()

    while True:
        # Window setup
        screen = pygame.display.set_mode((WIDTH, HEIGHT))

        result = main_menu(screen)

        if result == "Exit":
            break

        elif result == "New Alien":
            placed_parts, straight_angles = start_character_creater(screen)
            converted_guy = convert_ui_parts(placed_parts, straight_angles)
            config = create_neat_config(GuyMorphology(converted_guy.guy), "machineLearning/ml_config")
            evo_manager = EvolutionManager(config)
            winner = evo_manager.run(converted_guy, STEPS, DT, GENERATIONS)

            with open("winner.pkl", "wb") as file:
                pickle.dump(winner, file)
            print("winner")

            result = evo_manager.run_winner(winner, converted_guy, STEPS, DT, screen)
            if result != "main menu":
                break
        else:
            pass



if __name__ == "__main__":
    main()