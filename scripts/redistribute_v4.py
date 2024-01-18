
import os
import shutil
from pathlib import Path
from itertools import cycle

# Function to handle overwriting or renaming of files
def handle_file_conflict(source_file, target_file):
    if os.path.getsize(source_file) == os.path.getsize(target_file):
        # If the file with the same name has the same size, overwrite it
        print(f"Overwriting: {target_file} with {source_file}")
        shutil.move(source_file, target_file)
    else:
        # If the file with the same name has a different size, rename it
        base, extension = os.path.splitext(target_file)
        dup_count = 1
        while True:
            new_filename = f"{base}.dup{dup_count}{extension}"
            if not os.path.exists(new_filename):
                print(f"Renaming: {source_file} to {new_filename}")
                shutil.move(source_file, new_filename)
                break
            dup_count += 1

# Ask the user for the number of folders they want to redistribute into
try:
    num_folders = int(input("Enter the number of target folders for redistribution: "))
except ValueError:
    print("Please enter a valid integer for the number of folders.")
    exit()

# Define the base directories
source_dirs = [f"settlement_csvs{i}" for i in range(1, 256)]
aggregate_dir = "settlement_csvs"  # Single directory where all CSVs are initially moved
redistribute_dirs = [f"settlement_csvs{i}" for i in range(1, num_folders + 1)]

# Ensure the aggregate directory exists
Path(aggregate_dir).mkdir(parents=True, exist_ok=True)

# Move all CSV files from each source directory to the aggregate directory
for dir_path in source_dirs:
    path = Path(dir_path)
    if path.exists():
        for file_path in path.glob("*.csv"):
            target_file_path = Path(aggregate_dir) / file_path.name
            if target_file_path.exists():
                handle_file_conflict(file_path, target_file_path)
            else:
                print(f"Moving: {file_path} to {aggregate_dir}")
                shutil.move(str(file_path), str(target_file_path))

# Redistribute CSV files from the aggregate directory to the target directories evenly
csv_files = list(Path(aggregate_dir).glob("*.csv"))
target_dirs_cycle = cycle(redistribute_dirs)

for file_path in csv_files:
    target_dir = next(target_dirs_cycle)
    target_file_path = Path(target_dir) / file_path.name
    # Ensure the target directory exists
    Path(target_dir).mkdir(parents=True, exist_ok=True)
    if target_file_path.exists():
        handle_file_conflict(file_path, target_file_path)
    else:
        print(f"Distributing: {file_path} to {target_dir}")
        shutil.move(str(file_path), str(target_file_path))
