import os
from colorama import Fore, Back, Style, init

def print_with_session_number(session_number, message):
    print_colored_message(f"(#{session_number}): {message}")

def print_exception(session_number, e):
    print_exception_with_color(session_number, e)

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
