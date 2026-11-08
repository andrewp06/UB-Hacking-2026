
import multiprocessing
from pathlib import Path
import sys

import pygame
import pickle


from Game.main_menu import main_menu
from Game.char_adapter import convert_ui_parts
from Game.char_creator import start_character_creater, HEIGHT, WIDTH
from Game.sim_settings import get_simulation_settings
from machineLearning.guyMorphology import GuyMorphology
from machineLearning.dynamicConfig import create_neat_config
from machineLearning.evolutionManager import EvolutionManager

DT = 1/60



def get_base_dir() -> Path:
  # Resolves to _MEIPASS inside the .app, or your project root locally
  if hasattr(sys, "_MEIPASS"):
    return Path(sys._MEIPASS)
  return Path(__file__).resolve()

def main():
    pygame.init()
    pygame.font.init()
    remake = False
    while True:
        if not remake:
        # Window setup
            screen = pygame.display.set_mode((WIDTH, HEIGHT))

            result = main_menu(screen)

            if result == "Exit":
                break

        if result == "New Alien" or remake:
            
            if not remake:
                placed_parts, straight_angles = start_character_creater(screen)
                converted_guy = convert_ui_parts(placed_parts, straight_angles)

            remake = False

            settings = get_simulation_settings(screen, WIDTH)

            if settings is None:
                continue

            total_time, generations = settings

            dt = DT
            steps = int(total_time // DT)

            config = create_neat_config(
                GuyMorphology(converted_guy.guy),
                str(get_base_dir() /"machineLearning/ml_config")
            )

            evo_manager = EvolutionManager(config)

            winner = evo_manager.run(
                screen,
                converted_guy,
                steps,
                dt,
                generations
            )

            with open("winner.pkl", "wb") as file:
                pickle.dump(winner, file)

            result = evo_manager.run_winner(winner, converted_guy, steps, DT, screen)
            if result is None:
                break

            if result == "remake":
                remake = True

        else:
            pass


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()


