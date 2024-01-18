
import os
import shutil
from pathlib import Path
from itertools import cycle

# Ask the user for the number of folders they want to redistribute into
try:
    num_folders = int(input("Enter the number of folders you want to redistribute into: "))
except ValueError:
    print("Please enter a valid integer for the number of folders.")
    exit()

# Define the base directories
source_dirs = [f"settlement_csvs{i}" for i in range(1, num_folders + 1)]
target_dir = "settlement_csvs"

# Ensure the target directory exists
Path(target_dir).mkdir(parents=True, exist_ok=True)

# Move all CSV files from each source directory to the target directory, checking for duplicates
for dir_path in source_dirs:
    path = Path(dir_path)
    if path.exists():
        for file in path.glob("*.csv"):
            # Generate a new file name if a duplicate exists
            new_file_path = Path(target_dir) / file.name
            counter = 1
            while new_file_path.exists():
                new_file_path = Path(target_dir) / f"{file.stem}_{counter}{file.suffix}"
                counter += 1
            shutil.move(str(file), str(new_file_path))
