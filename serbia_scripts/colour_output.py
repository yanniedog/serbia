from colorama import Fore
import csv

def calculate_color(religion_weight, year_weight, state_weight, overall_weight):
    min_weight = min(religion_weight, year_weight, state_weight, overall_weight)
    max_weight = max(religion_weight, year_weight, state_weight, overall_weight)

    color_step = (Fore.RED, Fore.YELLOW, Fore.GREEN)
    normalized_weight = (overall_weight - min_weight) / (max_weight - min_weight)
    color_index = int(normalized_weight * (len(color_step) - 1))
    return color_step[color_index]

def color_text(color, text):
    return f"{color}{text}{Fore.RESET}"
