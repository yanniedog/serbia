from colorama import Fore, Style
import csv

def calculate_color(religion_weight, year_weight, state_weight, overall_weight):
    min_weight = min(religion_weight, year_weight, state_weight, overall_weight)
    max_weight = max(religion_weight, year_weight, state_weight, overall_weight)

    color_step = (Fore.RED, Fore.YELLOW, Fore.GREEN)
    if max_weight == min_weight:
        return color_step[len(color_step) // 2]
    normalized_weight = (overall_weight - min_weight) / (max_weight - min_weight)
    color_index = int(normalized_weight * (len(color_step) - 1))
    return color_step[color_index]

def color_text(color, text):
    return f"{color}{text}{Fore.RESET}"

def print_status_with_color(session_number, message, status, current_progress=None, total_progress=None,
                            religion_weight=1, year_weight=1, state_weight=1, overall_weight=4):
    if status == 'Downloaded':
        status_color = Fore.GREEN
    elif status == 'Exists':
        status_color = Fore.YELLOW
    elif status == 'Not Found':
        status_color = Fore.RED
    else:
        status_color = Fore.WHITE

    religion_color = calculate_color(religion_weight, year_weight, state_weight, overall_weight)
    year_color = calculate_color(year_weight, religion_weight, state_weight, overall_weight)
    state_color = calculate_color(state_weight, religion_weight, year_weight, overall_weight)
    overall_color = calculate_color(overall_weight, religion_weight, year_weight, state_weight)

    formatted = (
        f"[#{session_number}]: {message} - Religion: {color_text(religion_color, religion_weight)} "
        f"{status_color}{status}{Style.RESET_ALL} - Year: {color_text(year_color, year_weight)} "
        f"- State: {color_text(state_color, state_weight)} - Overall: {color_text(overall_color, overall_weight)}"
    )
    print(formatted)
